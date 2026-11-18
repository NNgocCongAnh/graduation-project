"""Specialized Agents for Procedural Case Generation & Localized Patch Repair.

Implements the multi-agent role decomposition from Paper 3 (arXiv:2604.11741):
1. OutlineAgent: Generates crime premise, victim forensics, and hidden Ground Truth.
2. CharacterAgent: Synthesizes suspects with distinct motives, alibis, and innocent secrets.
3. ClueAgent: Generates indirect physical traces, alibi-breaking crucial clues, and red herrings.
4. DeductionAgent (QaAgent): Synthesizes multi-hop reasoning chains connecting clues to culprit.

Each agent provides localized repair methods (Paper 7: ConWriter) to fix specific
constraint violations without discarding the entire narrative.
"""

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


class BaseAgent:
    """Base class for specialized generative agents."""

    FALLBACK_CANDIDATES = [
        ("http://localhost:20128/v1", "sk-9router-local", "gemini/gemma-4-31b-it"),
        ("http://localhost:20128/v1", "sk-9router-local", "gh/gpt-3.5-turbo-0613"),
        ("http://localhost:20128/v1", "sk-9router-local", "gh/gpt-4o-mini"),
        ("http://localhost:11434/v1", "ollama", "gemma4:e4b-it-qat"),
    ]

    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model
        self.last_used_model: str = model
        self.fallback_used: bool = False

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
        """Invoke a single LLM endpoint and parse non-empty JSON payload."""
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        raw_text = response.choices[0].message.content or "{}"
        clean_text = self._clean_json_string(raw_text)
        parsed = json.loads(clean_text)
        if not parsed:
            raise ValueError(f"Empty JSON object returned by model '{model}'")
        return parsed

    async def _call_llm_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call primary OpenAI-compatible LLM endpoint with per-agent smart fallback."""
        agent_name = self.__class__.__name__
        try:
            data = await self._invoke_single_model(self.client, self.model, system_prompt, user_prompt)
            self.last_used_model = self.model
            self.fallback_used = False
            return data
        except Exception as primary_err:
            logger.warning(f"[{agent_name}] Primary model '{self.model}' failed ({primary_err}). Initiating fallback chain...")

        primary_base = str(self.client.base_url).rstrip("/") if getattr(self.client, "base_url", None) else ""
        last_err: Optional[Exception] = None

        for fb_base, fb_key, fb_model in self.FALLBACK_CANDIDATES:
            if fb_model == self.model and fb_base.rstrip("/") == primary_base:
                continue
            try:
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
            "  1. Hồ sơ ban đầu có một 'Tiền đề sai lầm' (Flawed Initial Assumption): Cảnh sát điều tra cũ từng tin rằng án mạng xảy ra ở mốc giờ muộn (ví dụ 22:30) dựa vào tiếng động nhân chứng nghe thấy hoặc đồng hồ vỡ.\n"
            "  2. Người chơi BẮT BUỘC phải đọc Báo cáo giám định tử thi nhiệt học Henssge để tính ra: thời gian chết thực sự sớm hơn đáng kể (ví dụ 19:40 - 20:30).\n"
            "  3. Hung thủ chuẩn bị alibi cực kỳ hoàn hảo cho mốc 22:30 (mốc giờ giả), nhưng HOÀN TOÀN MẤT TÍCH hoặc có alibi mâu thuẫn trong khung giờ thực tế 19:40 - 20:30!\n"
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
            "  1. Biệt thự bị cô lập bởi trận mưa bão kinh hoàng. Nghi phạm khai chạy từ chòi vườn vào nhà chính lúc 20:45 để trú mưa.\n"
            "  2. Nhật ký khí tượng đo mưa (EV-04) cho thấy mưa xối xả làm ngập lối đi từ 20:10. Người đi qua lối đó bắt buộc phải ướt đẫm và dính bùn đỏ.\n"
            "  3. Giày và thảm chùi chân của nghi phạm hoàn toàn khô ráo, chứng minh nghi phạm chưa từng rời khỏi nhà chính mà đã nấp sẵn trong hành lang gây án."
        )
    elif any(k in t for k in ["hiện trường giả", "staged"]):
        return (
            "THỂ LOẠI: HIỆN TRƯỜNG GIẢ & ALIBI NGOẠI PHẠM DÀN DỰNG (STAGED CRIME)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (ĐÁNH LẠC HƯỚNG MỐC TỬ VONG BẰNG ĐỒNG HỒ PHÁ HỎNG):\n"
            "  1. Đồng hồ tại hiện trường bị đập vỡ cố tình dừng lại tại một mốc giờ cố định (ví dụ 21:40), kèm hiện trường giả như một vụ xô xát.\n"
            "  2. Toàn bộ nghi phạm đều có alibi cho mốc 21:40.\n"
            "  3. Người chơi BẮT BUỘC phải dùng định luật nguội lạnh Henssge để tính ra giờ chết thực tế là 19:30-20:30. Ai có alibi giả mạo mốc 21:40 nhưng 'mất tích' không có alibi trong khung 19:30-20:30 chính là hung thủ!"
        )
    else:
        return (
            "THỂ LOẠI: TRANH CHẤP QUYỀN LỢI & BÍ ẨN GIA TỘC (HIGH-SOCIETY DEDUCTION)\n"
            "- CƠ CHẾ ĐÁNH ĐỐ NÃO BỘ (MÂU THUẪN TRÌNH TỰ VĂN BẢN & PHÁP Y HỌC):\n"
            "  1. Hung thủ trưng ra tài liệu/di chúc/hợp đồng có chữ ký nạn nhân ở mốc giờ muộn (ví dụ 21:30).\n"
            "  2. Giám định y pháp chứng minh nạn nhân đã rơi vào trạng thái hôn mê sâu mất tri giác (hôn mê cấp) trước 20:00, không thể tự cầm bút ký văn bản.\n"
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
            "FORENSIC RULES: ambient_temp between 18.0 and 24.0°C; body_temp between 27.0 and 34.0°C. "
            "Also give body_weight_kg (45-120), cooling_factor (Henssge C: 1.0 clothed in still air, 0.8 lightly dressed/draughty, 1.2-1.3 under warm clothes/blanket) "
            "and discovery_time (HH:MM when the body was found and rectal temperature measured, typically 8-14 hours after the murder). "
            "Include rich forensic pathology details: livor_mortis_state, rigor_mortis_state, wound_description, cause_of_death, manner_of_death, clothing_state. "
            "The time-of-death window is recomputed by a Henssge physics engine from these values. "
            "ground_truth.actual_crime_time must fall inside this cooling window. "
            "ground_truth.culprit_id must be 'SUSP-01'."
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
      "ambient_temp": 18.5,
      "body_temp": 27.5,
      "livor_mortis_state": "Hoen tử thi tím sẫm cố định ở lưng, mông và mặt sau đùi, không phai màu khi ấn ngón tay.",
      "rigor_mortis_state": "Co cứng toàn phần (Full Rigor Mortis) ở cơ hàm, cổ và các khớp lớn ngoại biên.",
      "wound_description": "Vết đâm trực diện khoang liên sườn 4-5 bên trái sâu 8.5cm, thấu tim và rách quai động mạch chủ ngực.",
      "cause_of_death": "Sốc mất máu cấp tính do tổn thương thấu tim (Acute Hemorrhagic Shock).",
      "manner_of_death": "Vụ án mạng sát hại (Homicide).",
      "clothing_state": "Y phục nạn nhân còn nguyên vẹn, không có vết rách do xô xát vật lý trước đó.",
      "estimated_tod_start": "20:30",
      "estimated_tod_end": "20:50",
      "body_weight_kg": 76.0,
      "cooling_factor": 1.25,
      "discovery_time": "06:30"
    }}
  }},
  "ground_truth": {{
    "culprit_id": "SUSP-01",
    "actual_crime_time": "20:40",
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
        system_prompt = (
            "You are a Forensic Logic Repair Specialist. "
            "Fix the discrepancy between actual_crime_time and estimated_tod_start/estimated_tod_end based on diagnostic feedback. "
            "Output JSON with corrected 'forensic_data' and 'actual_crime_time'. "
            "FORENSIC PHYSICS RULE: When discovery_time is 06:30 and ambient_temp is 18.5°C, to have death occur around 20:30-20:50 the previous night (cooling time ~9.5-10.0 hours), "
            "body_temp MUST be between 31.5°C and 32.5°C (weight 70-80kg, cooling factor C=1.0). Never set body_temp close to ambient temperature!"
        )
        user_prompt = f"""
Current Forensic: {victim.forensic_data.model_dump_json()}
Current Crime Time: {ground_truth.actual_crime_time}
Diagnostic Violation: {diagnostic}
Requirement: Move actual_crime_time inside the valid Henssge cooling window (e.g. 20:40), and keep body_temp between 31.5°C and 32.5°C with cooling_factor 1.0.
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        if "forensic_data" in data:
            victim.forensic_data = ForensicData.model_validate(data["forensic_data"])
        if "actual_crime_time" in data:
            ground_truth.actual_crime_time = data["actual_crime_time"]
        return victim, ground_truth


class CharacterAgent(BaseAgent):
    """Responsible for generating suspects, personalities, alibis, and secrets."""

    async def generate(self, victim: Victim, ground_truth: GroundTruth, theme: str) -> List[Suspect]:
        guidance = _get_setting_guidance(theme)
        mechanic = _get_mystery_style_mechanic(theme)
        system_prompt = (
            "You are a Character Specialist in detective fiction (CharacterAgent). "
            "Generate 3 distinct, realistic suspects (SUSP-01, SUSP-02, SUSP-03). "
            "CRITICAL CULTURAL RULE: All suspect names MUST match the cultural background and nationality of the Victim (e.g. if Victim is Vietnamese, ALL suspect names MUST be authentic Vietnamese names. If British/Western, all names must be British). "
            "CRITICAL SETTING INTEGRITY RULE: Suspect occupations, residences, and alibi locations MUST strictly conform to the Setting Guidelines below. If the setting is a train, hospital, or ship, NEVER use manor/mansion tropes ('quản gia', 'thư phòng', 'lầu hai', 'lò sưởi', 'ban công'). "
            "CRITICAL MYSTERY DEDUCTION MECHANIC: Align suspects' timelines and statements with the Mystery Deduction Mechanic provided below. "
            "STRICT ANTI-GIVEAWAY / FAIR-PLAY RULES: "
            "1. SUSP-01 MUST have is_culprit = True (matches GroundTruth). "
            "2. SUSP-02 and SUSP-03 MUST have is_culprit = False. "
            "3. NO PHYSICAL SMOKING GUNS ON SUSPECTS: TUYỆT ĐỐI KHÔNG gán vết thương rớm máu, đứt tay, băng bó ngón tay, quần áo rách hay vết máu cho bất kỳ nghi phạm nào! Hung thủ SUSP-01 phải tỏ ra điềm tĩnh, ngoại hình gọn gàng, có vị thế đáng tin cậy. interview_notes chỉ mô tả phong thái tâm lý, thái độ điềm tĩnh hoặc né tránh ánh mắt khi bị hỏi sâu về lịch trình, và nhóm máu thông thường (không được biến nhóm máu thành chìa khóa suy luận đơn giản). "
            "4. SUSP-01's alibi statement claims an activity or location during actual_crime_time that seems completely plausible, but contains the specific documentary or environmental impossibility defined in the Mystery Deduction Mechanic (e.g. claiming a phone call while train is in a tunnel, or having dinner while delayed toxin was digesting). "
            "5. SUSP-02 and SUSP-03 MUST have strong motives and suspicious behavior (red herrings) that make them appear guilty, but their whereabouts during the ACTUAL Henssge crime window are verified by independent logs (witnesses, telephone switchboard, distant tickets)."
        )
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
    {{
      "id": "SUSP-01",
      "name": "<Họ tên nghi phạm 1 (Hung thủ) thuần bản địa>",
      "age": 48,
      "gender": "Nam",
      "occupation": "<Nghề nghiệp phù hợp bối cảnh>",
      "relationship_to_victim": "<Mối quan hệ với nạn nhân>",
      "residence": "<Vị trí/Khoang/Phòng cụ thể trong bối cảnh>",
      "motive": "<Động cơ gây án cụ thể>",
      "statement": "<Lời khai chi tiết về hoạt động ngoại phạm trong bối cảnh>",
      "timeline_claimed": "<Khung giờ ngoại phạm tại vị trí cụ thể>",
      "interview_notes": "<Ghi chú thẩm vấn: phong thái tâm lý điềm tĩnh, trả lời mạch lạc, né tránh ánh mắt khi nhắc đến mốc giờ gây án, Nhóm máu A/B/O/AB>",
      "alibi_start": "20:15",
      "alibi_end": "22:30",
      "alibi_statement": "<Hoạt động ngoại phạm chứa mâu thuẫn vật lý hoặc tài liệu sẽ bị bẻ gãy>",
      "secret_innocent_fact": null,
      "is_culprit": true,
      "image_url": "/static/assets/suspects/butler_male_50s.png"
    }},
    {{
      "id": "SUSP-02",
      "name": "<Họ tên nghi phạm 2 (Người vô tội có hành vi mờ ám riêng)>",
      "age": 39,
      "gender": "Nam",
      "occupation": "<Nghề nghiệp phù hợp bối cảnh>",
      "relationship_to_victim": "<Mối quan hệ với nạn nhân>",
      "residence": "<Vị trí/Khoang/Phòng cụ thể trong bối cảnh>",
      "motive": "<Động cơ đáng ngờ>",
      "statement": "<Lời khai về việc ở đâu trong khung giờ án mạng>",
      "timeline_claimed": "<Khung giờ ngoại phạm>",
      "interview_notes": "<Ghi chú thẩm vấn: thái độ căng thẳng, lo lắng về bí mật tài chính/tình cảm riêng, Nhóm máu A/B/O/AB>",
      "alibi_start": "21:15",
      "alibi_end": "22:45",
      "alibi_statement": "<Hoạt động ngoại phạm được người khác hoặc sổ sách xác nhận>",
      "secret_innocent_fact": "<Bí mật phi pháp hoặc riêng tư nhưng không giết người>",
      "is_culprit": false,
      "image_url": "/static/assets/suspects/businessman_male_50s.png"
    }},
    {{
      "id": "SUSP-03",
      "name": "<Họ tên nghi phạm 3 (Người vô tội bị nghi oan)>",
      "age": 26,
      "gender": "Nữ",
      "occupation": "<Nghề nghiệp phù hợp bối cảnh>",
      "relationship_to_victim": "<Mối quan hệ với nạn nhân>",
      "residence": "<Vị trí/Khoang/Phòng cụ thể trong bối cảnh>",
      "motive": "<Động cơ bị nghi ngờ>",
      "statement": "<Lời khai ngoại phạm>",
      "timeline_claimed": "<Khung giờ ngoại phạm>",
      "interview_notes": "<Ghi chú thẩm vấn: buồn bã hoặc sợ hãi, khẳng định vô tội, Nhóm máu A/B/O/AB>",
      "alibi_start": "20:30",
      "alibi_end": "22:00",
      "alibi_statement": "<Hoạt động ngoại phạm độc lập>",
      "secret_innocent_fact": "<Hành vi khả nghi nhưng độc lập với vụ án>",
      "is_culprit": false,
      "image_url": "/static/assets/suspects/female_30s.png"
    }}
  ]
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Suspect.model_validate(s) for s in data.get("suspects", [])]

    async def repair_suspects(self, suspects: List[Suspect], ground_truth: GroundTruth, diagnostic: str) -> List[Suspect]:
        """Localized patch repair for duplicate IDs or culprit flags (Paper 7)."""
        logger.info(f"[CharacterAgent] Applying localized patch repair: {diagnostic}")
        system_prompt = (
            "You are a Character Consistency Repair Agent. "
            "Fix suspect IDs or culprit assignment flaws based on the diagnostic feedback. "
            "Output JSON with corrected 'suspects' array. Exactly 1 suspect must have is_culprit=True matching culprit_id."
        )
        user_prompt = f"""
Current Suspects: {[s.model_dump() for s in suspects]}
Ground Truth Culprit ID: {ground_truth.culprit_id}
Diagnostic Violation: {diagnostic}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Suspect.model_validate(s) for s in data.get("suspects", [])]


class ClueAgent(BaseAgent):
    """Responsible for physical evidence, alibi-breaking clues, and red herrings."""

    async def generate(self, victim: Victim, suspects: List[Suspect], ground_truth: GroundTruth, theme: str) -> List[Evidence]:
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        guidance = _get_setting_guidance(theme)
        mechanic = _get_mystery_style_mechanic(theme)
        system_prompt = (
            "You are a Forensic Clue Specialist (ClueAgent). "
            "Generate 4 to 5 rich, objective physical evidences strictly found within the specific setting of the case. "
            "CRITICAL SETTING INTEGRITY RULE: Clue names, descriptions, and discovery locations MUST strictly match the Setting Guidelines. If on a train, clues must be on carriages/compartments/luggage racks; if in a hospital, wards/clinics/labs. DO NOT mention 'lò sưởi', 'thư phòng', 'ban công', 'ống khói' unless setting is an old manor! "
            "CRITICAL MYSTERY DEDUCTION MECHANIC: Follow the specific Mystery Deduction Mechanic provided below to craft intellectually challenging clues that require synthesizing multiple pieces of information. "
            "MULTI-HOP DEDUCTIVE DESIGN REQUIREMENTS: "
            "1. EV-01 (Timeline / Forensic Baseline - Crucial): A broken clock, dispatch log, medical monitor, or ambient record that was tampered with to show a false time, or medical toxicology indicating delayed reaction. Contradicts true Henssge Time of Death window. "
            "2. EV-02 (Red Herring for Suspect 2): An incriminating piece of evidence pointing to SUSP-02's secret non-murder wrongdoing within the setting, proving they did not commit the murder. "
            "3. EV-03 (Red Herring for Suspect 3): Suspicious physical trace of SUSP-03 in the setting, but independent verified records clear them during true TOD. "
            "4. EV-04 (Alibi-Breaking Environmental or Documentary Clue - Crucial): Objective physical state or official record that irrefutably refutes SUSP-01's claimed activity according to the Mystery Deduction Mechanic (e.g. railway tunnel transmission blackout log, cold appliance, intact blister pack, dry mud/drainage, unpunched tickets). "
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
      "title": "<Vật chứng red-herring nghi phạm 2>",
      "location": "<Vị trí phù hợp bối cảnh>",
      "description": "<Mô tả vật phẩm liên quan đến bí mật riêng của SUSP-02>",
      "is_weapon": false,
      "fingerprint_analysis": "<Dấu vân tay của SUSP-02 trên đồ vật>",
      "blood_dna_analysis": "Không phát hiện dấu vết máu.",
      "physical_condition": "<Chứng minh SUSP-02 chỉ phạm lỗi riêng chứ không liên quan đến cái chết của nạn nhân>",
      "linked_suspect_id": "SUSP-02",
      "is_crucial": false,
      "is_red_herring": true,
      "image_url": "/static/assets/evidences/evidence_sedative.png"
    }},
    {{
      "id": "EV-03",
      "title": "<Vật chứng red-herring nghi phạm 3>",
      "location": "<Vị trí phù hợp bối cảnh>",
      "description": "<Dấu vết để lại của SUSP-03>",
      "is_weapon": false,
      "fingerprint_analysis": "<Dấu vết của SUSP-03>",
      "blood_dna_analysis": "Không có dấu vết máu.",
      "physical_condition": "<Chứng minh SUSP-03 có chứng cứ ngoại phạm xác đáng trong khung giờ tử vong thực tế>",
      "linked_suspect_id": "SUSP-03",
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
        """Localized patch repair for missing crucial clue or unbroken alibi (Paper 7)."""
        logger.info(f"[ClueAgent] Applying localized patch repair: {diagnostic}")
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        system_prompt = (
            "You are a Forensic Clue Repair Specialist. "
            "The case validator flagged a flaw: missing crucial clue or unbroken culprit alibi. "
            "Modify or add an evidence item so there is at least one clear crucial clue (is_crucial=True) "
            "that definitively breaks the culprit's alibi. Output JSON with updated 'evidences' array."
        )
        user_prompt = f"""
Culprit: {culprit.id} ({culprit.name})
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
      "inference": "Các nghi phạm SUSP-02 và SUSP-03 được loại trừ trong khung giờ tử vong thực tế nhờ có chứng cứ ngoại phạm độc lập và tài liệu đối chiếu xác nhận không có mặt tại hiện trường.",
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
