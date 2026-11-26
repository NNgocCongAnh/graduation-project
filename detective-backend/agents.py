"""Specialized Agents for Procedural Case Generation & Localized Patch Repair.

Implements the multi-agent role decomposition from Paper 3 (arXiv:2604.11741):
1. OutlineAgent: Generates crime premise, victim forensics, and hidden Ground Truth.
2. CharacterAgent: Synthesizes suspects with distinct motives, alibis, and innocent secrets.
3. ClueAgent: Generates indirect physical traces, alibi-breaking crucial clues, and red herrings.
4. DeductionAgent (QaAgent): Synthesizes multi-hop reasoning chains connecting clues to culprit.

Each agent provides localized repair methods (Paper 7: ConWriter) to fix specific
constraint violations without discarding the entire narrative.
"""

import os

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from pydantic import ValidationError

from models import (
    Victim, Suspect, Evidence, GroundTruth, ForensicData,
    ReasoningChain, DeductionStep, ConstraintViolation
)

logger = logging.getLogger(__name__)


# Placeholder resolved at call time to the LLM_API_KEY env var (never hardcoded).
_GATEWAY_KEY = "<LLM_API_KEY>"


class BaseAgent:
    """Base class for specialized generative agents."""

    FALLBACK_CANDIDATES = [
        ("http://localhost:20128/v1", _GATEWAY_KEY, "gemini/gemma-4-31b-it"),
        ("http://localhost:20128/v1", _GATEWAY_KEY, "gh/gpt-3.5-turbo-0613"),
        ("http://localhost:20128/v1", _GATEWAY_KEY, "gh/gpt-4o-mini"),
        ("http://localhost:11434/v1", "ollama", "gemma4:e4b-it-qat"),
    ]

    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model
        self.last_used_model: str = model
        self.fallback_used: bool = False
        self.last_usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.last_payload_tokens: int = 0

    @staticmethod
    def _clean_json_string(text: str) -> str:
        """Strip markdown code blocks, reasoning traces, and extract outermost JSON."""
        import re
        text = text.strip()
        # Strip thinking blocks from reasoning models
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        # Strip markdown fences
        if "```" in text:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return match.group(1)
        # Fallback to outermost braces
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]
        return text

    async def _invoke_single_model(self, client: AsyncOpenAI, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Invoke a single LLM endpoint and parse non-empty JSON payload with automatic 429 backoff."""
        # Calculate local text payload token footprint (~1.33 tokens per word)
        self.last_payload_tokens = int(len((system_prompt + " " + user_prompt).split()) * 1.33)

        max_attempts = max(1, int(os.getenv("AGENT_MAX_429_ATTEMPTS", "8")))
        last_exc: Optional[Exception] = None
        for attempt in range(max_attempts):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )
                # Capture API token telemetry
                usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                if getattr(response, "usage", None):
                    usage_info["prompt_tokens"] = getattr(response.usage, "prompt_tokens", 0) or 0
                    usage_info["completion_tokens"] = getattr(response.usage, "completion_tokens", 0) or 0
                    usage_info["total_tokens"] = getattr(response.usage, "total_tokens", 0) or 0
                self.last_usage = usage_info

                raw_text = response.choices[0].message.content or "{}"
                clean_text = self._clean_json_string(raw_text)
                parsed = json.loads(clean_text)
                if not parsed:
                    raise ValueError(f"Empty JSON object returned by model '{model}'")
                return parsed
            except Exception as e:
                last_exc = e
                err_msg = str(e).lower()
                if "429" in err_msg or "rate limit" in err_msg or "too many requests" in err_msg:
                    import re, asyncio
                    m_min_sec = re.search(r'reset after (\d+)m\s*(\d+)s', err_msg)
                    m_sec = re.search(r'reset after (\d+)s', err_msg)
                    if m_min_sec:
                        backoff = float(int(m_min_sec.group(1)) * 60 + int(m_min_sec.group(2)) + 2)
                    elif m_sec:
                        backoff = float(int(m_sec.group(1)) + 2)
                    else:
                        backoff = float((attempt + 1) * 5.0)
                    logger.warning(f"Rate limited (429) on model '{model}'. Waiting {backoff:.1f}s for reset window (attempt {attempt+1}/{max_attempts})...")
                    await asyncio.sleep(backoff)
                else:
                    raise e
        raise last_exc or RuntimeError(f"Failed to invoke model '{model}' after {max_attempts} attempts.")

    async def _call_llm_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call primary OpenAI-compatible LLM endpoint with per-agent smart fallback."""
        agent_name = self.__class__.__name__
        try:
            data = await self._invoke_single_model(self.client, self.model, system_prompt, user_prompt)
            self.last_used_model = self.model
            self.fallback_used = False
            return data
        except Exception as primary_err:
            if os.getenv("DISABLE_AGENT_FALLBACK", "0") == "1":
                raise RuntimeError(f"[{agent_name}] Primary model '{self.model}' failed (fallback disabled): {primary_err}") from primary_err
            logger.warning(f"[{agent_name}] Primary model '{self.model}' failed ({primary_err}). Initiating fallback chain...")

        primary_base = str(self.client.base_url).rstrip("/") if getattr(self.client, "base_url", None) else ""
        last_err: Optional[Exception] = None

        for fb_base, fb_key, fb_model in self.FALLBACK_CANDIDATES:
            if fb_model == self.model and fb_base.rstrip("/") == primary_base:
                continue
            try:
                if fb_key == _GATEWAY_KEY:
                    fb_key = os.getenv("LLM_API_KEY", "").strip()
                fb_client = AsyncOpenAI(base_url=fb_base, api_key=fb_key)
                data = await self._invoke_single_model(fb_client, fb_model, system_prompt, user_prompt)
                self.last_used_model = fb_model
                self.fallback_used = True
                logger.warning(f"[{agent_name}] Fallback activated: '{self.model}' -> '{fb_model}'")
                return data
            except Exception as fb_err:
                last_err = fb_err
                logger.warning(f"[{agent_name}] Fallback model '{fb_model}' failed ({fb_err}).")

        raise RuntimeError(f"[{agent_name}] All primary and fallback models failed. Last error: {last_err}")


def _get_setting_guidance(theme: str) -> str:
    """Extract and build strict setting-specific ontology rules to prevent Manor hallucination."""
    t = theme.lower()
    if any(k in t for k in ["tàu", "train", "đường sắt", "thống nhất", "toa"]):
        return (
            "BỐI CẢNH ĐOÀN TÀU HỎA / CHUYẾN TÀU ĐÊM:\n"
            "- Hiện trường & Nơi ở: Phải là các vị trí trên tàu (Khoang giường nằm VIP số X, Buồng lái đầu máy, Toa hành lý, Toa hàng ăn, Hành lang nối toa).\n"
            "- Nghề nghiệp & Quan hệ: Toa trưởng, Nhân viên soát vé, Phục vụ toa ăn, Kỹ sư đầu máy, Hành khách đồng hành (thương nhân, du khách).\n"
            "- Lời khai & Alibi: Kiểm tra vé hành khách, phục vụ bữa ăn khuya tại toa ăn, nghỉ ngơi trong khoang kín.\n"
            "- Manh mối & Hung khí: Đồng hồ buồng tàu bị dừng, sổ kiểm vé, bếp điện/ấm nước toa ăn nguội lạnh chưa bật, dao/hung khí giấu sau tấm lưới thông gió toa hành lý.\n"
            "- CẤM TUYỆT ĐỐI: Không dùng 'thư phòng', 'lầu hai', 'lò sưởi', 'ban công', 'quản gia', 'biệt thự'!"
        )
    elif any(k in t for k in ["bệnh viện", "hospital", "phòng khám", "viện điều dưỡng"]):
        return (
            "BỐI CẢNH BỆNH VIỆN / PHÒNG KHÁM:\n"
            "- Hiện trường & Nơi ở: Phòng bệnh nhân VIP, Phòng trực cấp cứu, Kho dược phẩm, Phòng xét nghiệm y khoa, Khu vực phẫu thuật.\n"
            "- Nghề nghiệp & Quan hệ: Bác sĩ điều trị, Y tá ca trực, Dược sĩ phụ trách kho, Thân nhân bệnh nhân, Viện trưởng.\n"
            "- Lời khai & Alibi: Đi phát thuốc ca đêm, trực phòng lưu bệnh nhân, kiểm kê sổ sách dược phẩm.\n"
            "- Manh mối & Hung khí: Thiết bị theo dõi sinh hiệu bị can thiệp giờ, sổ trực thiếu trang, khay kim tiêm/dao mổ giấu trong thùng rác y tế.\n"
            "- CẤM TUYỆT ĐỐI: Không dùng 'thư phòng', 'lầu hai', 'lò sưởi', 'ban công', 'quản gia'!"
        )
    elif any(k in t for k in ["thuyền", "tàu thủy", "cruise", "du thuyền", "biển"]):
        return (
            "BỐI CẢNH DU THUYỀN / TÀU THỦY BIỂN:\n"
            "- Hiện trường & Nơi ở: Cabin thượng hạng boong A, Buồng hoa tiêu, Phòng máy hầm tàu, Nhà hàng salon, Boong dạo ngắm biển.\n"
            "- Nghề nghiệp & Quan hệ: Thuyền phó, Thủy thủ trưởng, Kỹ sư máy tàu, Phục vụ quầy bar, Hành khách khoang VIP.\n"
            "- Lời khai & Alibi: Kiểm tra ca trực buồng lái, bảo trì động cơ ở boong đáy, phục vụ rượu tại salon.\n"
            "- Manh mối & Hung khí: Nhật ký hải trình bị tẩy xóa, van máy lạnh ngắt, hung khí giấu trong ngăn phao cứu sinh.\n"
            "- CẤM TUYỆT ĐỐI: Không dùng 'thư phòng', 'lò sưởi', 'quản gia'!"
        )
    elif any(k in t for k in ["công ty", "văn phòng", "tập đoàn", "viện nghiên cứu", "lab", "trụ sở"]):
        return (
            "BỐI CẢNH TRỤ SỞ TẬP ĐOÀN / VIỆN NGHIÊN CỨU:\n"
            "- Hiện trường & Nơi ở: Phòng họp giám đốc, Phòng server dữ liệu, Phòng lab nghiên cứu, Bàn làm việc open-space, Phòng bảo vệ.\n"
            "- Nghề nghiệp & Quan hệ: Giám đốc điều hành, Trợ lý dự án, Kỹ sư phần mềm, Nhân viên bảo vệ, Đối tác cổ đông.\n"
            "- Lời khai & Alibi: Quẹt thẻ ra vào cổng kiểm soát, giám sát batch máy chủ, duyệt hồ sơ tài chính đêm muộn.\n"
            "- Manh mối & Hung khí: Nhật ký cửa điện tử bị ngắt nguồn, nhiệt độ phòng máy chủ bất thường, hung khí giấu trong trần kỹ thuật.\n"
            "- CẤM TUYỆT ĐỐI: Không dùng 'thư phòng', 'lò sưởi', 'quản gia', 'biệt thự'!"
        )
    else:
        return (
            "BỐI CẢNH KHUÔN VIÊN TRANG VIÊN / BIỆT THỰ / NHÀ RIÊNG:\n"
            "- Hiện trường: Phòng làm việc, phòng khách, phòng nghỉ, hoa viên.\n"
            "- Nghề nghiệp & Quan hệ: Quản gia, bác sĩ riêng, người thân gia đình, người thừa kế, luật sư.\n"
            "- Manh mối: Đồng hồ vỡ, tài liệu cháy, dấu vết hiện trường, hung khí giấu kín."
        )


def _get_mystery_style_mechanic(theme: str) -> str:
    """Define distinct, intellectually demanding deduction mechanics based on mystery genre & difficulty."""
    t = theme.lower()
    if any(k in t for k in ["chưa có lời giải", "cold case", "độ khó cao", "hồ sơ lạnh"]):
        return (
            "THỂ LOẠI: VỤ ÁN HỒ SƠ LẠNH - ĐỘ KHÓ CAO (COLD CASE - MAXIMUM DIFFICULTY)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (MÂU THUẪN MA TRẬN TÀI LIỆU & NGHỊCH LÝ THỜI GIAN):\n"
            "  1. Hồ sơ ban đầu có một 'Tiền đề sai lầm' (Flawed Initial Assumption): Cảnh sát điều tra cũ từng tin rằng án mạng xảy ra ở mốc giờ muộn dựa vào tiếng động nhân chứng nghe thấy hoặc đồng hồ bị phá hỏng.\n"
            "  2. Người chơi BẮT BUỘC phải đọc Báo cáo giám định tử thi nhiệt học Henssge để tính ra: thời gian chết thực sự sớm hơn đáng kể so với giả định ban đầu.\n"
            "  3. Hung thủ chuẩn bị alibi cực kỳ hoàn hảo cho mốc giờ ngụy tạo đó, nhưng HOÀN TOÀN MẤT TÍCH hoặc có alibi mâu thuẫn trong khung giờ tử vong thực tế do Henssge xác định!\n"
            "  4. TUYỆT ĐỐI KHÔNG để lộ sơ hở rẻ tiền như 'vết đứt tay rớm máu' hay 'sợi chỉ tạp dề'. Hung thủ phải tỏ ra vô can, điềm tĩnh, có vị thế đáng tin cậy.\n"
            "  5. Điểm mâu thuẫn cốt lõi (EV-04): Bản ghi chép nhật ký viễn thông hoặc sổ đối chiếu khách quan chứng minh hung thủ không hề ở nơi đã khai trong khung giờ Henssge thực tế."
        )
    elif any(k in t for k in ["tàu", "train", "đường sắt", "chuyến tàu"]):
        return (
            "THỂ LOẠI: KỲ ÁN TRÊN CHUYẾN TÀU ĐÊM / HÀNH TRÌNH CÔ LẬP\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (MÂU THUẪN LỊCH TRÌNH CHẠY TÀU & ĐIỂM CHẾT TÍN HIỆU):\n"
            "  1. Hung thủ khai rằng trong khung giờ án mạng đang gọi điện thoại đường dài hoặc gửi thông điệp trong khoang riêng.\n"
            "  2. Tuy nhiên, nhật ký điều độ chạy tàu & bản đồ địa hình (EV-04) ghi nhận đoàn tàu lúc đó đang đi qua hầm núi dài/khu vực đèo mất hoàn toàn sóng vô tuyến viễn thông.\n"
            "  3. Hung thủ không thể thực hiện bất kỳ cuộc gọi nào trong thời gian tàu xuyên hầm đèo.\n"
            "  4. Người chơi phải kết hợp: Báo cáo giờ tử thi Henssge + Bảng lịch trình giờ tàu chạy qua các hầm để phát hiện lời khai ngoại phạm là bất khả thi về mặt vật lý!"
        )
    elif any(k in t for k in ["phòng kín", "locked-room", "locked room"]):
        return (
            "THỂ LOẠI: ÁN MẠNG PHÒNG KÍN CỔ ĐIỂN (LOCKED-ROOM MYSTERY)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (NGHỊCH LÝ THỜI GIAN TÁC ĐỘNG & BẪY KHÓA TRONG):\n"
            "  1. Căn phòng/khoang kín bị khóa chốt then cài từ BÊN TRONG, chìa khóa duy nhất nằm trong túi nạn nhân.\n"
            "  2. Điểm 'vắt óc': Hung thủ không hề đột nhập hay tẩu thoát khỏi phòng kín! Hung thủ đã ra tay từ TRƯỚC (khiến nạn nhân bị chấn thương sọ não kín hoặc xuất huyết âm ỉ), sau đó nạn nhân tự đi vào phòng khóa cửa đi ngủ và tử vong sau đó vài giờ.\n"
            "  3. Người ở cùng nạn nhân trước khi cửa bị khóa chặt mới là hung thủ thực sự, phá tan ảo tưởng phòng kín."
        )
    elif any(k in t for k in ["đầu độc", "poison"]):
        return (
            "THỂ LOẠI: ĐẦU ĐỘC BÍ ẨN KHÔNG MÀU KHÔNG MÙI (PHARMACOKINETIC DELAY)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (ĐỘ TRỄ DƯỢC ĐỘNG HỌC & TIÊU HÓA DẠ DÀY):\n"
            "  1. Nạn nhân ngã gục tử vong trong lúc đang ngồi uống trà cùng nghi phạm khác. Mọi nghi ngờ đổ dồn vào tách trà uống dở.\n"
            "  2. Tuy nhiên kết quả độc chất tử thi chứng minh: Chất độc nằm trong viên nang bao tan trong ruột (enteric-coated) mất 90-120 phút mới rã trong tá tràng.\n"
            "  3. Bữa ăn chứa viên thuốc độc đã được dung nạp từ 2 tiếng trước. Kẻ dọn bữa ăn/thuốc trước đó mới là hung thủ thực sự, loại trừ hoàn toàn những người có mặt lúc nạn nhân ngã gục!"
        )
    elif any(k in t for k in ["hung khí biến mất", "vanishing weapon", "mất dấu"]):
        return (
            "THỂ LOẠI: HUNG KHÍ BIẾN MẤT KHÔNG DẤU VẾT (VANISHING WEAPON)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (VẬT LIỆU CHUYỂN PHA HOẶC CẢI TRANG CÔNG CỤ CHỨC NĂNG):\n"
            "  1. Khám nghiệm hiện trường không tìm thấy bất kỳ dao hay vật nhọn nào.\n"
            "  2. Tuy nhiên, vết thương có kích thước hình học đặc thù của một vật dụng cơ khí/trang trí chức năng đã được lau sạch đặt lại vị trí cũ, hoặc cọc đá tuyết carbon dioxide / dung dịch muối băng tan chảy thành nước bốc hơi để lại cặn khoáng tại phễu thoát sàn (EV-04).\n"
            "  3. Hung thủ là người duy nhất có chuyên môn và quyền tiếp cận hệ thống thiết bị/vật liệu đặc thù đó."
        )
    elif any(k in t for k in ["biệt thự cô lập", "mưa bão", "isolated manor"]):
        return (
            "THỂ LOẠI: BIỆT THỰ CÔ LẬP GIỮA ĐÊM MƯA BÃO (ISOLATED MANOR)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (DẤU VẾT VI MÔ MÔI TRƯỜNG & LỊCH TRÌNH MƯA BÃO):\n"
            "  1. Biệt thự bị cô lập bởi trận mưa bão kinh hoàng. Nghi phạm khai chạy qua lối sân vườn vào nhà chính để trú mưa ngay trước thời điểm phát hiện thi thể.\n"
            "  2. Nhật ký khí tượng đo mưa (EV-04) cho thấy mưa xối xả làm ngập toàn bộ lối đi sân vườn từ trước đó rất lâu. Người đi qua lối đó bắt buộc phải ướt đẫm và dính bùn đỏ.\n"
            "  3. Giày và thảm chùi chân của nghi phạm hoàn toàn khô ráo, chứng minh nghi phạm chưa từng rời khỏi nhà chính mà đã nấp sẵn trong hành lang gây án."
        )
    elif any(k in t for k in ["hiện trường giả", "staged"]):
        return (
            "THỂ LOẠI: HIỆN TRƯỜNG GIẢ & ALIBI NGOẠI PHẠM DÀN DỰNG (STAGED CRIME)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (ĐÁNH LẠC HƯỚNG MỐC TỬ VONG BẰNG ĐỒNG HỒ PHÁ HỎNG):\n"
            "  1. Đồng hồ hoặc thiết bị tại hiện trường bị cố ý phá hỏng dừng lại tại một mốc giờ sắp đặt, kèm hiện trường ngụy tạo xô xát.\n"
            "  2. Toàn bộ nghi phạm đều chuẩn bị alibi cho mốc đồng hồ vỡ.\n"
            "  3. Người chơi BẮT BUỘC phải dùng định luật nguội lạnh Henssge để tính ra giờ chết thực tế sớm hơn đáng kể. Kẻ có alibi hoàn hảo cho mốc đồng hồ vỡ nhưng không có bằng chứng ngoại phạm hợp lệ trong khung giờ chết thực tế chính là hung thủ!\n"
            "  4. Mốc thời gian gây án thực tế actual_crime_time cần được chọn linh hoạt và phân tán tự nhiên trong khoảng 18:00 - 23:59."
        )
    elif any(k in t for k in ["cybertech", "công nghệ cao", "phòng thí nghiệm", "lab", "server"]):
        return (
            "THỂ LOẠI: PHÒNG THÍ NGHIỆM CÔNG NGHỆ CAO / VỤ ÁN AN NINH MẠNG\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (NHẬT KÝ ĐIỆN TỬ, NHIỆT ĐỘ PHÒNG LẠNH SERVER & QUẸT THẺ TỪ):\n"
            "  1. Nạn nhân được tìm thấy trong phòng server lạnh hoặc phòng thí nghiệm kín với điều hòa nhiệt độ ổn định.\n"
            "  2. Hung thủ tạo lập chứng cứ ngoại phạm số tinh vi (gửi email hẹn giờ, quẹt thẻ từ giả danh tại cổng an ninh).\n"
            "  3. Tuy nhiên, thời gian tử vong xác định qua định luật Henssge (tính theo nhiệt độ phòng lạnh 18-20°C) mâu thuẫn hoàn toàn với thời điểm dữ liệu số được phát tán.\n"
            "  4. Manh mối then chốt chứng minh thiết bị truy cập được điều khiển từ xa hoặc thẻ an ninh đã bị sao chép."
        )
    else:
        return (
            "THỂ LOẠI: TRANH CHẤP QUYỀN LỢI & BÍ ẨN GIA TỘC (HIGH-SOCIETY DEDUCTION)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (MÂU THUẪN TRÌNH TỰ VĂN BẢN & PHÁP Y HỌC):\n"
            "  1. Hung thủ trưng ra tài liệu/di chúc/hợp đồng có chữ ký nạn nhân ở mốc giờ muộn hơn thời điểm tử vong thực tế.\n"
            "  2. Giám định y pháp chứng minh nạn nhân đã rơi vào trạng thái mất tri giác hoặc đã tử vong trước thời điểm ghi trên văn bản, không thể tự cầm bút ký văn bản.\n"
            "  3. Văn bản là sản phẩm giả mạo hoặc cưỡng ép sau khi nạn nhân đã mất khả năng nhận thức."
        )


class OutlineAgent(BaseAgent):
    """Responsible for setting, victim forensics, and secret Ground Truth."""

    async def generate(self, theme: str) -> Tuple[str, str, Victim, GroundTruth]:
        guidance = _get_setting_guidance(theme)
        mechanic = _get_mystery_style_mechanic(theme)
        system_prompt = (
            "You are a Master Mystery Architect (OutlineAgent). "
            "Your task is to establish a locked-room mystery outline, victim forensic data, and the absolute Ground Truth. "
            "CRITICAL CULTURAL RULE: All names (victim name, suspects), locations, and vocabulary MUST be authentic and strictly match the Country and Culture specified in the Theme (e.g. if Vietnam, victim MUST have a realistic Vietnamese name like 'Nguyễn Văn Hải', 'Trần Đình Trọng', 'Lê Hữu Đạt', etc. NEVER use English names like 'Arthur Blackwood' unless theme is in UK). "
            "CRITICAL SETTING INTEGRITY RULE: The victim discovery site, residence, and summary MUST strictly adhere to the setting ontology (e.g. Train -> sleeping cabin, passenger berth; Hospital -> ward/room). DO NOT mention 'thư phòng', 'lầu hai', 'lò sưởi' unless theme is an old manor! "
            "CRITICAL DEDUCTION MECHANIC: Establish the ground_truth.core_contradiction strictly following the Mystery Deduction Mechanic provided below. Avoid cheap giveaways. "
            "Output JSON with title, summary, victim (name, age, gender, occupation, residence, forensic_data), and ground_truth. "
            "FORENSIC RULES: ambient_temp between 18.0 and 24.0°C. "
            "If the murder occurred the previous night (between 19:00 and 23:30) and the body was discovered the next morning (07:00-08:30), "
            "cooling time is approximately 8 to 12 hours. For standard body weight (65-85kg, cooling_factor C=1.0) and ambient temp 18-22°C, "
            "the measured rectal body_temp MUST be between 30.5°C and 33.5°C (do NOT set body_temp below 29.5°C). "
            "Also give body_weight_kg (45-120), cooling_factor (Henssge C: 1.0 clothed in still air, 0.8 lightly dressed/draughty, 1.2-1.3 under warm clothes/blanket) "
            "and discovery_time (HH:MM between 07:00 and 08:30 when the body was found and rectal temperature measured). "
            "Include rich forensic pathology details: livor_mortis_state, rigor_mortis_state, wound_description, cause_of_death, manner_of_death, clothing_state. "
            "The time-of-death window is recomputed by a Henssge physics engine from these values. "
            "ground_truth.actual_crime_time must fall inside this cooling window (typically between 18:00 and 23:59). "
            "ground_truth.culprit_id should select one suspect identifier ('SUSP-01', 'SUSP-02', or 'SUSP-03') to ensure balanced diversity across cases."
        )
        user_prompt = f"""
Theme: {theme}
Setting Guidelines:
{guidance}

Mystery Deduction Mechanic:
{mechanic}

Format:
{{
  "title": "<Tên vụ án tiếng Việt hấp dẫn phù hợp chủ đề>",
  "summary": "<Mô tả bối cảnh vụ án phòng kín 2-3 câu sát thực tế>",
  "victim": {{
    "name": "<Họ tên nạn nhân bản địa chuẩn xác>",
    "age": 62,
    "gender": "Nam",
    "occupation": "<Nghề nghiệp phù hợp bối cảnh>",
    "residence": "<Địa chỉ / Vị trí cụ thể trong bối cảnh>",
    "forensic_data": {{
      "ambient_temp": 20.0,
      "body_temp": 31.5,
      "livor_mortis_state": "Hoen tử thi tím sẫm cố định ở lưng, mông và mặt sau đùi, không phai màu khi ấn ngón tay.",
      "rigor_mortis_state": "Co cứng toàn phần (Full Rigor Mortis) ở cơ hàm, cổ và các khớp lớn ngoại biên.",
      "wound_description": "Vết đâm trực diện khoang liên sườn 4-5 bên trái sâu 8.5cm, thấu tim và rách quai động mạch chủ ngực.",
      "cause_of_death": "Sốc mất máu cấp tính do tổn thương thấu tim (Acute Hemorrhagic Shock).",
      "manner_of_death": "Vụ án mạng sát hại (Homicide).",
      "clothing_state": "Y phục nạn nhân còn nguyên vẹn, không có vết rách do xô xát vật lý trước đó.",
      "estimated_tod_start": "<Giờ ước lượng HH:MM>",
      "estimated_tod_end": "<Giờ ước lượng HH:MM>",
      "body_weight_kg": 70.0,
      "cooling_factor": 1.0,
      "discovery_time": "08:00"
    }}
  }},
  "ground_truth": {{
    "culprit_id": "<Mã định danh nghi phạm hung thủ: chọn một trong SUSP-01, SUSP-02, hoặc SUSP-03>",
    "actual_crime_time": "<Mốc giờ gây án thực tế HH:MM nằm trong khoảng thời gian tử vong tính toán của Henssge (thường từ 18:00 đến 23:59)>",
    "murder_weapon": "<Tên hung khí cụ thể>",
    "core_contradiction": "<Mâu thuẫn then chốt giữa lời khai ngoại phạm của hung thủ và manh mối vật lý hiện trường>"
  }}
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        victim = Victim.model_validate(data["victim"])
        ground_truth = GroundTruth.model_validate(data["ground_truth"])
        return data.get("title", "Án Mạng Bí Ẩn"), data.get("summary", ""), victim, ground_truth

    async def repair_tod(self, victim: Victim, ground_truth: GroundTruth, diagnostic: str) -> Tuple[Victim, GroundTruth]:
        """Localized patch repair for TOD / Crime Time violations (Paper 7)."""
        logger.info(f"[OutlineAgent] Applying localized patch repair: {diagnostic}")
        from validator import henssge_tod_window
        window = henssge_tod_window(victim.forensic_data)
        start_str, end_str = ("20:30", "23:30")
        mid_str = "21:30"
        if window:
            start_str, end_str = window
            try:
                sh, sm = map(int, start_str.split(':'))
                eh, em = map(int, end_str.split(':'))
                stot = sh * 60 + sm
                etot = eh * 60 + em
                if etot < stot:
                    etot += 1440
                mid_tot = (stot + etot) // 2 % 1440
                mid_str = f"{mid_tot // 60:02d}:{mid_tot % 60:02d}"
            except Exception:
                pass

        system_prompt = (
            "You are a Forensic Logic Repair Specialist. "
            "Fix the discrepancy between actual_crime_time and the valid Henssge Time of Death window. "
            "Output JSON with corrected 'forensic_data' and 'actual_crime_time'. "
            "FORENSIC PHYSICS RULE: body_temp MUST be between 30.5°C and 33.5°C (warmer than ambient_temp 18.0-22.0°C). "
            f"actual_crime_time MUST be set to a time inside [{start_str} - {end_str}]."
        )
        user_prompt = f"""
Current Forensic: {victim.forensic_data.model_dump_json()}
Current Crime Time: {ground_truth.actual_crime_time}
Valid Henssge Calculated TOD Window: [{start_str} - {end_str}]
Recommended Crime Time: '{mid_str}'
Diagnostic Violation: {diagnostic}
Requirement: Keep ambient_temp (~20°C) and body_temp (~31.5°C) physically sound. Move actual_crime_time into [{start_str} - {end_str}].
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        if "forensic_data" in data:
            candidate_fd = ForensicData.model_validate(data["forensic_data"])
            if candidate_fd.body_temp > candidate_fd.ambient_temp + 2.0:
                victim.forensic_data = candidate_fd
        if "actual_crime_time" in data:
            ground_truth.actual_crime_time = data["actual_crime_time"]
        return victim, ground_truth


class CharacterAgent(BaseAgent):
    """Responsible for generating suspects, personalities, alibis, and secrets."""

    async def generate(self, victim: Victim, ground_truth: GroundTruth, theme: str, enable_post_processing: bool = True) -> List[Suspect]:
        guidance = _get_setting_guidance(theme)
        mechanic = _get_mystery_style_mechanic(theme)

        # Parse crime time to provide realistic relative guidance
        c_time = ground_truth.actual_crime_time or "20:40"
        try:
            c_h, c_m = map(int, c_time.split(':'))
            crime_mins = c_h * 60 + c_m
        except Exception:
            crime_mins = 20 * 60 + 40
        sug_culprit_start = f"{max(0, crime_mins - 25) // 60:02d}:{max(0, crime_mins - 25) % 60:02d}"
        sug_culprit_end = f"{min(1439, crime_mins + 35) // 60:02d}:{min(1439, crime_mins + 35) % 60:02d}"
        sug_innocent1_start = f"{max(0, crime_mins - 50) // 60:02d}:{max(0, crime_mins - 50) % 60:02d}"
        sug_innocent1_end = f"{min(1439, crime_mins + 15) // 60:02d}:{min(1439, crime_mins + 15) % 60:02d}"
        sug_innocent2_start = f"{max(0, crime_mins + 10) // 60:02d}:{max(0, crime_mins + 10) % 60:02d}"
        sug_innocent2_end = f"{min(1439, crime_mins + 70) // 60:02d}:{min(1439, crime_mins + 70) % 60:02d}"

        target_culprit_id = ground_truth.culprit_id if ground_truth.culprit_id in ["SUSP-01", "SUSP-02", "SUSP-03"] else "SUSP-01"

        system_prompt = (
            "You are a Character Specialist in detective fiction (CharacterAgent). "
            "Generate 3 distinct, realistic suspects (SUSP-01, SUSP-02, SUSP-03). "
            "CRITICAL CULTURAL RULE: All suspect names MUST match the cultural background and nationality of the Victim (e.g. if Victim is Vietnamese, ALL suspect names MUST be authentic Vietnamese names. If British/Western, all names must be British). "
            "CRITICAL SETTING INTEGRITY RULE: Suspect occupations, residences, and alibi locations MUST strictly conform to the Setting Guidelines below. If the setting is a train, hospital, or ship, NEVER use manor/mansion tropes ('quản gia', 'thư phòng', 'lầu hai', 'lò sưởi', 'ban công'). "
            "CRITICAL STATEMENT ACTION & RICHNESS RULE: Every suspect's `statement` MUST describe concrete tasks, physical actions, and sensory interactions (e.g. 'đang pha ấm trà hoa cúc và kiểm kê 15 kiện hàng số 4', 'đang ghi chép sổ lộ trình chuyến tàu và nghe thấy tiếp viên gõ cửa khoang bên', 'đang sửa chữa van áp suất đồng hồ số 2'). TUYỆT ĐỐI KHÔNG chỉ nói cộc lốc 'Tôi ở phòng X từ giờ Y đến Z'. Lời khai phải có đồ vật cụ thể, âm thanh hoặc người đi qua để người chơi có dữ kiện bóc tách mâu thuẫn. "
            f"CRITICAL TIMELINE INTEGRITY RULE: For {target_culprit_id} (Culprit), `alibi_start` and `alibi_end` MUST strictly bracket actual_crime_time (e.g. start 15-30 mins BEFORE crime time, end 30-50 mins AFTER crime time). `statement` MUST open with the EXACT interval 'Từ [alibi_start] đến [alibi_end], tôi đang [hành động cụ thể] tại [vị trí]...'. TUYỆT ĐỐI KHÔNG gán mốc giờ trong statement lệch khỏi alibi_start và alibi_end. "
            "CRITICAL MYSTERY DEDUCTION MECHANIC: Align suspects' timelines and statements with the Mystery Deduction Mechanic provided below. "
            "STRICT ANTI-GIVEAWAY / FAIR-PLAY RULES: "
            f"1. The suspect with id '{target_culprit_id}' MUST have is_culprit = True (matches GroundTruth). "
            "2. The remaining suspects MUST have is_culprit = False. "
            "3. NO PHYSICAL SMOKING GUNS ON SUSPECTS: TUYỆT ĐỐI KHÔNG gán vết thương rớm máu, đứt tay, băng bó ngón tay, quần áo rách hay vết máu cho bất kỳ nghi phạm nào! Hung thủ phải tỏ ra điềm tĩnh, ngoại hình gọn gàng, có vị thế đáng tin cậy. interview_notes chỉ mô tả phong thái tâm lý, thái độ điềm tĩnh hoặc né tránh ánh mắt khi bị hỏi sâu về lịch trình, và nhóm máu thông thường. "
            f"4. {target_culprit_id}'s alibi statement claims an activity or location during actual_crime_time that seems completely plausible, but contains the specific documentary or environmental impossibility defined in the Mystery Deduction Mechanic. "
            "5. Innocent suspects MUST have strong motives and suspicious behavior (red herrings) that make them appear guilty, but their whereabouts during the ACTUAL Henssge crime window are verified by independent logs."
        )

        def make_susp_spec(sid: str, name_hint: str, role_hint: str, age: int, gender: str, occ: str, sug_s: str, sug_e: str, img: str):
            is_c = (sid == target_culprit_id)
            if is_c:
                return f'''    {{
      "id": "{sid}",
      "name": "<Họ tên {sid} (Hung thủ) thuần bản địa>",
      "age": {age},
      "gender": "{gender}",
      "occupation": "<{occ}>",
      "relationship_to_victim": "<Mối quan hệ với nạn nhân>",
      "residence": "<Vị trí/Khoang/Phòng cụ thể trong bối cảnh>",
      "motive": "<Động cơ gây án cụ thể>",
      "statement": "Từ {sug_culprit_start} đến {sug_culprit_end}, tôi ở <residence> đang <mô tả hành động công việc cụ thể, chi tiết đồ vật/âm thanh/tương tác>.",
      "timeline_claimed": "{sug_culprit_start} - {sug_culprit_end}",
      "interview_notes": "<Ghi chú thẩm vấn: phong thái tâm lý điềm tĩnh, trả lời mạch lạc, né tránh ánh mắt khi nhắc đến mốc giờ gây án, Nhóm máu A/B/O/AB>",
      "alibi_start": "{sug_culprit_start}",
      "alibi_end": "{sug_culprit_end}",
      "alibi_statement": "<Hoạt động ngoại phạm chứa mâu thuẫn vật lý hoặc tài liệu sẽ bị bẻ gãy>",
      "secret_innocent_fact": null,
      "is_culprit": true,
      "image_url": "{img}"
    }}'''
            else:
                return f'''    {{
      "id": "{sid}",
      "name": "<Họ tên {sid} (Người vô tội) thuần bản địa>",
      "age": {age},
      "gender": "{gender}",
      "occupation": "<{occ}>",
      "relationship_to_victim": "<Mối quan hệ với nạn nhân>",
      "residence": "<Vị trí/Khoang/Phòng cụ thể trong bối cảnh>",
      "motive": "<Động cơ đáng ngờ>",
      "statement": "Từ {sug_s} đến {sug_e}, tôi ở <residence> đang <mô tả hành động cụ thể>.",
      "timeline_claimed": "{sug_s} - {sug_e}",
      "interview_notes": "<Ghi chú thẩm vấn: thái độ lo lắng về bí mật riêng, Nhóm máu A/B/O/AB>",
      "alibi_start": "{sug_s}",
      "alibi_end": "{sug_e}",
      "alibi_statement": "<Hoạt động ngoại phạm được người khác hoặc sổ sách xác nhận>",
      "secret_innocent_fact": "<Bí mật phi pháp hoặc riêng tư nhưng không giết người>",
      "is_culprit": false,
      "image_url": "{img}"
    }}'''

        s1_json = make_susp_spec("SUSP-01", "Nghi phạm 1", "Quản gia / Trợ lý", 48, "Nam", "Nghề nghiệp phù hợp bối cảnh", sug_innocent1_start, sug_innocent1_end, "/static/assets/suspects/butler_male_50s.png")
        s2_json = make_susp_spec("SUSP-02", "Nghi phạm 2", "Bác sĩ / Kỹ sư", 39, "Nam", "Nghề nghiệp phù hợp bối cảnh", sug_innocent1_start, sug_innocent1_end, "/static/assets/suspects/businessman_male_50s.png")
        s3_json = make_susp_spec("SUSP-03", "Nghi phạm 3", "Nữ thừa kế / Nhân viên", 26, "Nữ", "Nghề nghiệp phù hợp bối cảnh", sug_innocent2_start, sug_innocent2_end, "/static/assets/suspects/female_30s.png")

        user_prompt = f"""
Theme: {theme}
Setting Guidelines:
{guidance}

Mystery Deduction Mechanic:
{mechanic}

Victim: {victim.name}, {victim.age} tuổi, {victim.occupation}
Ground Truth: Culprit={ground_truth.culprit_id}, Crime Time={ground_truth.actual_crime_time}, Flaw={ground_truth.core_contradiction}

Output JSON (all professions and residences MUST strictly fit {theme}):
{{
  "suspects": [
{s1_json},
{s2_json},
{s3_json}
  ]
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        suspects = [Suspect.model_validate(s) for s in data.get("suspects", [])]

        if enable_post_processing:
            # Post-Processing: Deterministic Synchronization of Timeline and Action Statement
            for s in suspects:
                s.timeline_claimed = f"{s.alibi_start} - {s.alibi_end}"

                # Enforce culprit alibi bracket
                if s.is_culprit and ground_truth.actual_crime_time:
                    try:
                        c_h, c_m = map(int, ground_truth.actual_crime_time.split(':'))
                        c_tot = c_h * 60 + c_m
                        s_h, s_m = map(int, s.alibi_start.split(':'))
                        e_h, e_m = map(int, s.alibi_end.split(':'))
                        s_tot = s_h * 60 + s_m
                        e_tot = e_h * 60 + e_m
                        if not (s_tot <= c_tot <= e_tot):
                            s.alibi_start = sug_culprit_start
                            s.alibi_end = sug_culprit_end
                            s.timeline_claimed = f"{s.alibi_start} - {s.alibi_end}"
                    except Exception:
                        pass

                # Synchronize statement prefix with exact alibi interval
                if s.statement:
                    prefix = f"Từ {s.alibi_start} đến {s.alibi_end}"
                    if prefix not in s.statement and f"{s.alibi_start} - {s.alibi_end}" not in s.statement:
                        # Clean out any conflicting arbitrary time from the front
                        cleaned = re.sub(
                            r'^(Tôi|Tôi đã|Vào lúc|Khoảng|Từ)?\s*(ở|tại)?\s*.*?(từ|lúc|khoảng)?\s*\d{1,2}:\d{2}.*?(đến|cho đến khi)?\s*(\d{1,2}:\d{2}|kết thúc)?[\.,;:]?\s*',
                            '',
                            s.statement,
                            flags=re.IGNORECASE
                        ).strip()
                        if not cleaned:
                            cleaned = f"ở {s.residence} làm việc và không rời khỏi đây"
                        s.statement = f"{prefix}, tôi {cleaned}"
        else:
            # Without post-processing: keep raw alibi and statement as produced by LLM
            for s in suspects:
                if not s.timeline_claimed:
                    s.timeline_claimed = f"{s.alibi_start} - {s.alibi_end}"

        return suspects

    async def repair_suspects(self, suspects: List[Suspect], ground_truth: GroundTruth, diagnostic: str) -> List[Suspect]:
        """Localized patch repair for duplicate IDs, culprit flags, or broken alibi bracketing (Paper 7)."""
        logger.info(f"[CharacterAgent] Applying localized patch repair: {diagnostic}")
        system_prompt = (
            "You are a Character Consistency Repair Agent. "
            "Fix suspect IDs, culprit flags, or alibi bracketing flaws based on the diagnostic feedback. "
            f"REQUIREMENTS: "
            f"1. Unique IDs: Each suspect must have a unique ID (SUSP-01, SUSP-02, SUSP-03). "
            f"2. Culprit: Exactly 1 suspect must have is_culprit=True with id='{ground_truth.culprit_id}'. "
            f"3. Alibi Bracket: The culprit's alibi_start and alibi_end MUST bracket actual_crime_time ('{ground_truth.actual_crime_time}'). "
            "4. Rich Statement: Preserve each suspect's full statement (must be >= 6 words). "
            "Output JSON with corrected 'suspects' array."
        )
        user_prompt = f"""
Current Suspects: {[s.model_dump() for s in suspects]}
Ground Truth Culprit ID: {ground_truth.culprit_id}
Actual Crime Time: {ground_truth.actual_crime_time}
Diagnostic Violation: {diagnostic}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        repaired = [Suspect.model_validate(s) for s in data.get("suspects", [])]
        for s in repaired:
            s.timeline_claimed = f"{s.alibi_start} - {s.alibi_end}"
        return repaired


class ClueAgent(BaseAgent):
    """Responsible for physical evidence, alibi-breaking clues, and red herrings."""

    async def generate(self, victim: Victim, suspects: List[Suspect], ground_truth: GroundTruth, theme: str) -> List[Evidence]:
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        # Red herrings must point at INNOCENT suspects, whichever ID the culprit has.
        innocents = [s.id for s in suspects if s.id != culprit.id] + ["SUSP-02", "SUSP-03"]
        innocent_a, innocent_b = innocents[0], innocents[1]
        guidance = _get_setting_guidance(theme)
        mechanic = _get_mystery_style_mechanic(theme)
        system_prompt = (
            "You are a Forensic Clue Specialist (ClueAgent). "
            "Generate 4 to 5 rich, objective physical evidences strictly found within the specific setting of the case. "
            "CRITICAL SETTING INTEGRITY RULE: Clue names, descriptions, and discovery locations MUST strictly match the Setting Guidelines. If on a train, clues must be on carriages/compartments/luggage racks; if in a hospital, wards/clinics/labs. DO NOT mention 'lò sưởi', 'thư phòng', 'ban công', 'ống khói' unless setting is an old manor! "
            "CRITICAL MYSTERY DEDUCTION MECHANIC: Follow the specific Mystery Deduction Mechanic provided below to craft intellectually challenging clues that require synthesizing multiple pieces of information. "
            "MULTI-HOP DEDUCTIVE DESIGN REQUIREMENTS: "
            "1. EV-01 (Timeline / Forensic Baseline - Crucial): A broken clock, dispatch log, medical monitor, or ambient record that was tampered with to show a false time, or medical toxicology indicating delayed reaction. Contradicts true Henssge Time of Death window. "
            f"2. EV-02 (Red Herring for innocent suspect {innocent_a}): An incriminating piece of evidence pointing to {innocent_a}'s secret non-murder wrongdoing within the setting, proving they did not commit the murder. "
            f"3. EV-03 (Red Herring for innocent suspect {innocent_b}): Suspicious physical trace of {innocent_b} in the setting, but independent verified records clear them during true TOD. "
            f"4. EV-04 (Alibi-Breaking Environmental or Documentary Clue - Crucial): Objective physical state or official record that irrefutably refutes the culprit {culprit.id}'s claimed activity according to the Mystery Deduction Mechanic (e.g. railway tunnel transmission blackout log, cold appliance, intact blister pack, dry mud/drainage, unpunched tickets). "
            "5. EV-05 (Murder Weapon - Crucial): The hidden weapon concealed in an environment-appropriate hiding spot (e.g. air duct, maintenance panel, cargo crate). The forensic lab analysis must report ONLY objective technical parameters: weapon blade/edge dimensions matching the wound, blood matching victim, and specialized industrial/chemical traces (e.g. machine grease, carriage brake dust, marine lubricant) that link logically to the culprit's domain of access. "
            "STRICT FAIR-PLAY & ZERO-SPOILER RULES: "
            "- NEVER state the suspect's name, ID, or direct identity in fingerprint_analysis or blood_dna_analysis! "
            "- NEVER use cheap giveaways like 'sợi chỉ từ tạp dề của hung thủ' or 'vết máu từ ngón tay đứt của hung thủ'! The connection must be multi-hop: Forensic Autopsy -> True TOD window -> Alibi impossibility via EV-04 -> Exclusive weapon access/specialized trace via EV-05!"
        )
        user_prompt = f"""
Theme: {theme}
Setting Guidelines:
{guidance}

Mystery Deduction Mechanic:
{mechanic}

Victim: {victim.name}, Wounds: {victim.forensic_data.wound_description}
Culprit: {culprit.id} ({culprit.name}), Alibi: "{culprit.alibi_statement}" [{culprit.alibi_start}-{culprit.alibi_end}]
Ground Truth Contradiction: {ground_truth.core_contradiction}

Output JSON with 5 distinct evidences strictly located in {theme}:
{{
  "evidences": [
    {{
      "id": "EV-01",
      "title": "<Tên thiết bị ghi giờ/đồng hồ bị can thiệp làm sai lệch thời gian hoặc tài liệu mốc giờ ban đầu>",
      "location": "<Vị trí phát hiện tại hiện trường>",
      "description": "<Mô tả mặt kính vỡ hoặc thiết bị bị dừng lại ở mốc thời gian giả>",
      "is_weapon": false,
      "fingerprint_analysis": "<Dấu vết cơ học hoặc vân tay mờ của nạn nhân>",
      "blood_dna_analysis": "Không phát hiện dấu vết máu hay dịch sinh học.",
      "physical_condition": "<Kiểm định cơ học/kỹ thuật chứng minh mốc giờ bị cố tình can thiệp làm giả hoặc mâu thuẫn nhiệt học>",
      "linked_suspect_id": null,
      "is_crucial": true,
      "is_red_herring": false,
      "image_url": "/static/assets/evidences/pocket_watch_broken.png"
    }},
    {{
      "id": "EV-02",
      "title": "<Vật chứng red-herring của nghi phạm vô tội {innocent_a}>",
      "location": "<Vị trí phù hợp bối cảnh>",
      "description": "<Mô tả vật phẩm liên quan đến bí mật riêng của {innocent_a}>",
      "is_weapon": false,
      "fingerprint_analysis": "<Dấu vân tay của {innocent_a} trên đồ vật>",
      "blood_dna_analysis": "Không phát hiện dấu vết máu.",
      "physical_condition": "<Chứng minh {innocent_a} chỉ phạm lỗi riêng chứ không liên quan đến cái chết của nạn nhân>",
      "linked_suspect_id": "{innocent_a}",
      "is_crucial": false,
      "is_red_herring": true,
      "image_url": "/static/assets/evidences/evidence_sedative.png"
    }},
    {{
      "id": "EV-03",
      "title": "<Vật chứng red-herring của nghi phạm vô tội {innocent_b}>",
      "location": "<Vị trí phù hợp bối cảnh>",
      "description": "<Dấu vết để lại của {innocent_b}>",
      "is_weapon": false,
      "fingerprint_analysis": "<Dấu vết của {innocent_b}>",
      "blood_dna_analysis": "Không có dấu vết máu.",
      "physical_condition": "<Chứng minh {innocent_b} có chứng cứ ngoại phạm xác đáng trong khung giờ tử vong thực tế>",
      "linked_suspect_id": "{innocent_b}",
      "is_crucial": false,
      "is_red_herring": true,
      "image_url": "/static/assets/evidences/evidence_letter.png"
    }},
    {{
      "id": "EV-04",
      "title": "<Vật chứng môi trường hoặc tài liệu đối chiếu lật tẩy alibi hung thủ>",
      "location": "<Vị trí nơi hung thủ khai đang ở hoặc tài liệu điều độ khách quan>",
      "description": "<Mô tả hiện trạng vật lý khách quan hoặc văn bản nhật ký>",
      "is_weapon": false,
      "fingerprint_analysis": "Dấu vết bám bụi tự nhiên, không có dấu vết vận hành trong khung giờ gây án.",
      "blood_dna_analysis": "Không có máu.",
      "physical_condition": "<Tình trạng vật lý hoặc tài liệu chứng minh hung thủ không thể thực hiện hoạt động như đã khai>",
      "linked_suspect_id": "{culprit.id}",
      "is_crucial": true,
      "is_red_herring": false,
      "image_url": "/static/assets/evidences/evidence_teacup.png"
    }},
    {{
      "id": "EV-05",
      "title": "<Hung khí thật sự giấu kín>",
      "location": "<Vị trí giấu kín kín đáo phù hợp bối cảnh>",
      "description": "<Mô tả hung khí có kích thước và hình dáng trùng khớp vết thương nạn nhân>",
      "is_weapon": true,
      "fingerprint_analysis": "Dấu vân tay bị lau chùi cẩn thận, phát hiện vi vết dầu mỡ bảo dưỡng cơ khí chuyên dụng.",
      "blood_dna_analysis": "Mũi hung khí dính máu trùng khớp ADN nạn nhân. Không có máu ngoại lai.",
      "physical_condition": "<Kích thước hung khí (chiều dài, bản rộng) hoàn toàn tương thích với vết thương tử vong trong báo cáo pháp y>",
      "linked_suspect_id": "{culprit.id}",
      "is_crucial": true,
      "is_red_herring": false,
      "image_url": "/static/assets/evidences/evidence_knife.png"
    }}
  ]
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Evidence.model_validate(e) for e in data.get("evidences", [])]

    async def repair_clues(self, evidences: List[Evidence], suspects: List[Suspect], ground_truth: GroundTruth, diagnostic: str) -> List[Evidence]:
        """Localized patch repair for missing crucial clues, broken alibis, or referential schema errors (Paper 7)."""
        logger.info(f"[ClueAgent] Applying localized patch repair: {diagnostic}")
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        valid_suspect_ids = [s.id for s in suspects]
        system_prompt = (
            "You are a Forensic Clue Repair Specialist. "
            "Fix evidence flaws according to the diagnostic feedback. "
            "REQUIREMENTS: "
            f"1. Referential Integrity: Every evidence linked_suspect_id MUST be one of {valid_suspect_ids} or null. "
            f"2. Fair-Play: Crucial evidence (is_crucial=True) MUST link to culprit '{culprit.id}' or null; NEVER link crucial clues to innocent suspects! "
            f"3. Solvability: At least 1 crucial clue (is_crucial=True, is_red_herring=False) MUST definitively break {culprit.id}'s alibi. "
            "Output JSON with updated 'evidences' array containing 4 to 5 evidences."
        )
        user_prompt = f"""
Culprit: {culprit.id} ({culprit.name})
All Suspects: {[{'id': s.id, 'name': s.name, 'is_culprit': s.is_culprit} for s in suspects]}
Culprit Claimed Alibi: "{culprit.alibi_statement}" [{culprit.alibi_start} - {culprit.alibi_end}]
Core Contradiction: {ground_truth.core_contradiction}
Current Evidences: {[e.model_dump() for e in evidences]}
Diagnostic Violation: {diagnostic}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Evidence.model_validate(e) for e in data.get("evidences", [])]


class DeductionAgent(BaseAgent):
    """Synthesizes the multi-hop reasoning chain proving solvability (Paper 3 QaAgent)."""

    async def generate(self, victim: Victim, suspects: List[Suspect], evidences: List[Evidence], ground_truth: GroundTruth, theme: str = "") -> ReasoningChain:
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        innocents = [s.id for s in suspects if s.id != culprit.id] + ["SUSP-02", "SUSP-03"]
        innocent_a, innocent_b = innocents[0], innocents[1]
        crucial_clues = [e.id for e in evidences if e.is_crucial]
        ev_summary_str = "\n".join([f"- {e.id}: {e.title} tại {e.location} (crucial={e.is_crucial}, weapon={e.is_weapon})" for e in evidences])
        mechanic = _get_mystery_style_mechanic(theme) if theme else ""
        system_prompt = (
            "You are a Chief Detective Logic Synthesizer (DeductionAgent). "
            "Construct a 4-step Multi-Hop Reasoning Chain proving how the player solves this case. "
            "Hop 1: Disprove the fabricated or apparent crime scene timestamp using Henssge body cooling window. "
            "Hop 2: Exonerate the innocent suspects by cross-verifying their alibis and independent records during the true TOD window. "
            "Hop 3: Expose the culprit's fabricated alibi via the physical environmental or documentary contradiction (EV-04). "
            "Hop 4: Form the decisive material link connecting the hidden weapon's location and specialized forensic traces to the culprit. "
            "CRITICAL LANGUAGE RULE: Every field ('inference', 'final_conclusion', 'decisive_contradiction') MUST be written strictly in academic Vietnamese (tiếng Việt). NEVER output English sentences in inference or conclusion!"
        )
        user_prompt = f"""
Theme: {theme}
Mystery Deduction Mechanic:
{mechanic}

Victim: {victim.name}, Estimated TOD: {victim.forensic_data.estimated_tod_start} - {victim.forensic_data.estimated_tod_end}
Culprit: {culprit.id} ({culprit.name}), Claim: "{culprit.alibi_statement}"
Available Evidences:
{ev_summary_str}
Crucial Clues Available: {crucial_clues}
Core Contradiction: {ground_truth.core_contradiction}

Output JSON (all inferences must refer to the actual clues above):
{{
  "steps": [
    {{
      "step_number": 1,
      "clue_ids": ["EV-01"],
      "inference": "Mốc thời gian trên EV-01 là hiện trường giả mạo hoặc nhận định ban đầu sai lệch, mâu thuẫn hoàn toàn với kết quả nhiệt học tử thi Henssge xác định thời điểm tử vong thực tế từ {victim.forensic_data.estimated_tod_start} đến {victim.forensic_data.estimated_tod_end}.",
      "target_suspect_id": null
    }},
    {{
      "step_number": 2,
      "clue_ids": ["EV-02", "EV-03"],
      "inference": "Các nghi phạm {innocent_a} và {innocent_b} được loại trừ trong khung giờ tử vong thực tế nhờ có chứng cứ ngoại phạm độc lập và tài liệu đối chiếu xác nhận không có mặt tại hiện trường.",
      "target_suspect_id": null
    }},
    {{
      "step_number": 3,
      "clue_ids": ["EV-04"],
      "inference": "Hiện trạng vật lý tại EV-04 bác bỏ hoàn toàn lời khai của {culprit.name} rằng đang ở vị trí ngoại phạm trong khung giờ gây án thực tế.",
      "target_suspect_id": "{culprit.id}"
    }},
    {{
      "step_number": 4,
      "clue_ids": ["EV-05"],
      "inference": "Hung khí EV-05 được giấu kín có đặc tính kỹ thuật, kích thước tương thích với vết thương tử vong và vị trí giấu thuộc quyền tiếp cận độc quyền của {culprit.name}.",
      "target_suspect_id": "{culprit.id}"
    }}
  ],
  "final_conclusion": "{culprit.name} đã sát hại nạn nhân trong khung giờ {victim.forensic_data.estimated_tod_start}-{victim.forensic_data.estimated_tod_end}, cố ý tạo lập chứng cứ ngoại phạm giả, nhưng bị lật tẩy bởi mâu thuẫn vật lý hiện trường và hung khí bị phát hiện.",
  "decisive_contradiction": "{ground_truth.core_contradiction}"
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return ReasoningChain.model_validate(data)
