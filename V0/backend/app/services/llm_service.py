import json
import logging
import random
from typing import Dict, Any
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.core.config import settings
from app.schemas.case_schema import GeneratedCaseSchema

logger = logging.getLogger(__name__)

# BỘ DỮ LIỆU KỊCH BẢN MẪU ĐA DẠNG (DYNAMIC SEED CASES POOL)
DYNAMIC_SEED_CASES = [
  {
    "title": "Bí Ẩn Vụ Án Mạng Tại Biệt Thự Cổ Blackwood",
    "summary": "Vào đêm mưa bão ngày 15/10, ngài Arthur Blackwood - nhà sưu tầm cổ vật giàu có - được phát hiện tử vong tại phòng làm việc khóa kín trên tầng 2 của biệt thự.",
    "difficulty": "Medium",
    "victim": {
        "name": "Arthur Blackwood",
        "age": 62,
        "occupation": "Nhà sưu tầm cổ vật & Doanh nhân",
        "body_condition": "Tử thi nằm gục trên bàn làm việc. Nhiệt độ cơ thể giảm xuống còn 31.2°C (nhiệt độ môi trường 22°C), hoen tử thi cố định rõ ở vùng lưng và đùi. Vết thương thấu ngực do vật nhọn.",
        "location_found": "Phòng làm việc tầng 2, Biệt thự Blackwood"
    },
    "suspects": [
        {
            "name": "Quản gia William",
            "age": 55,
            "occupation": "Quản gia biệt thự",
            "motive": "Tranh chấp tiền lương và sắp bị ngài Arthur sa thải do làm hỏng đồ cổ.",
            "alibi": "Khẳng định lúc 21:00 - 22:00 đang chuẩn bị trà ở dưới bếp tầng 1 và không lên tầng 2.",
            "persona": "Trầm lặng, lịch thiệp nhưng ẩn chứa sự bất mãn kéo dài.",
            "is_culprit": False
        },
        {
            "name": "Julian Blackwood",
            "age": 28,
            "occupation": "Nhiếp ảnh gia tự do",
            "motive": "Nợ nần cờ bạc chồng chất, ngài Arthur vừa từ chối gạch tên Julian khỏi di chúc.",
            "alibi": "Khai rằng từ 21:15 đến 21:45 đang ở phòng đọc sách tầng 1 nói chuyện điện thoại.",
            "persona": "Cháu trai nạn nhân, nông nổi, hoang phí, thường xuyên cãi lộn với nạn nhân.",
            "is_culprit": True
        },
        {
            "name": "Bác sĩ Eleanor Vance",
            "age": 42,
            "occupation": "Bác sĩ gia đình",
            "motive": "Nạn nhân phát hiện bác sĩ kê đơn thuốc giả để trục lợi bảo hiểm.",
            "alibi": "Khai rằng thăm khám cho nạn nhân lúc 20:30 và rời biệt thự lúc 21:00.",
            "persona": "Thông minh, quyết đoán, giữ thái độ hợp tác với cảnh sát.",
            "is_culprit": False
        }
    ],
    "timeline": [
        {"event_time": "20:30 - 21:00", "description": "Bác sĩ Eleanor thăm khám sức khỏe cho ngài Arthur tại phòng làm việc tầng 2.", "location": "Phòng làm việc", "character_name": "Eleanor Vance"},
        {"event_time": "21:00 - 21:15", "description": "Quản gia William mang trà lên phòng ngài Arthur, sau đó trở xuống bếp.", "location": "Tầng 1 & Tầng 2", "character_name": "Quản gia William"},
        {"event_time": "21:20 - 21:35", "description": "Julian lên tầng 2 lén lút vào phòng làm việc cãi nhau với nạn nhân và sát hại.", "location": "Phòng làm việc", "character_name": "Julian Blackwood"},
        {"event_time": "22:00", "description": "Quản gia phát hiện thi thể nạn nhân qua khe cửa phòng làm việc.", "location": "Phòng làm việc", "character_name": "Quản gia William"}
    ],
    "evidences": [
        {"item_name": "Mảnh thủy tinh vỡ dính máu", "description": "Mảnh kính của chiếc đồng hồ đeo tay bị vỡ tìm thấy dưới gầm bàn.", "location_found": "Dưới bàn làm việc", "related_character_name": "Julian Blackwood", "is_key_evidence": True},
        {"item_name": "Tách trà cúc La Mã", "description": "Tách trà uống dở trên bàn, không phát hiện độc chất.", "location_found": "Mặt bàn làm việc", "related_character_name": "Quản gia William", "is_key_evidence": False},
        {"item_name": "Sợi chỉ đỏ giắt vào cửa sổ", "description": "Cửa sổ hướng ra ban công đóng không chặt, giắt một sợi chỉ từ áo len đỏ.", "location_found": "Khe cửa sổ tầng 2", "related_character_name": "Julian Blackwood", "is_key_evidence": True}
    ],
    "culprit_name": "Julian Blackwood",
    "forensic_report": "Báo cáo khám nghiệm hiện trường & tử thi:\n- Tử thi nạn nhân Arthur Blackwood (62 tuổi) nằm sấp tại phòng làm việc.\n- Nhiệt độ tử thi đo được lúc 22:30 là 31.2°C. Nhiệt độ môi trường phòng 22°C.\n- Hoen tử thi xuất hiện ở vùng lưng và mông, đã cố định hoàn toàn.\n- Nguyên nhân tử vong trực tiếp: Mất máu cấp do vết thương xuyên thấu ngực bởi vật nhọn."
  },
  {
    "title": "Án Mạng Trong Đêm Tại Quán Bar Jazz Midnight",
    "summary": "Nữ ca sĩ nhạc Jazz quyến rũ Scarlet Laurent bị sát hại tại phòng hóa trang sau đêm diễn cuối tuần.",
    "difficulty": "Hard",
    "victim": {
        "name": "Scarlet Laurent",
        "age": 31,
        "occupation": "Ca sĩ nhạc Jazz phòng trà",
        "body_condition": "Thi thể gục trên bàn trang điểm. Nhiệt độ tử thi đo được lúc 01:00 sáng là 34.0°C (nhiệt độ phòng 24°C). Dấu vết siết cổ bằng dây kim loại mảnh.",
        "location_found": "Phòng hóa trang hậu đài Quán Bar Midnight"
    },
    "suspects": [
        {
            "name": "Victor Moreau",
            "age": 45,
            "occupation": "Chủ quán Bar Midnight",
            "motive": "Scarlet chuẩn bị hủy hợp đồng biểu diễn để chuyển sang quán bar đối thủ.",
            "alibi": "Khai rằng lúc 23:00 - 23:30 đang thu tiền tại quầy thu ngân tầng 1.",
            "persona": "Thâm trầm, tính toán, quản lý tài chính nghiêm ngặt.",
            "is_culprit": True
        },
        {
            "name": "Henri Dupont",
            "age": 34,
            "occupation": "Nhạc công Piano",
            "motive": "Bị Scarlet từ chối tình cảm nhiều lần công khai trước ban nhạc.",
            "alibi": "Khai rằng lúc 23:15 đang ở phòng thu âm phía sau sân khấu thử nốt nhạc.",
            "persona": "Nghệ sĩ lãng mạn, dễ kích động.",
            "is_culprit": False
        }
    ],
    "timeline": [
        {"event_time": "22:30 - 23:00", "description": "Scarlet hoàn thành bài hát biểu diễn cuối cùng và lui vào hậu trường.", "location": "Sân khấu Bar", "character_name": "Scarlet Laurent"},
        {"event_time": "23:10 - 23:25", "description": "Victor bước vào phòng hóa trang tranh cãi về hợp đồng và dùng dây đàn siết cổ nạn nhân.", "location": "Phòng hóa trang", "character_name": "Victor Moreau"}
    ],
    "evidences": [
        {"item_name": "Sợi dây đàn Piano đứt văng dưới sàn", "description": "Dây đàn số 3 có dính vết vân tay mờ của người quản lý.", "location_found": "Gầm bàn trang điểm", "related_character_name": "Victor Moreau", "is_key_evidence": True},
        {"item_name": "Vết son môi trên ly rượu Whisky", "description": "Ly rượu nghi dính độc nhưng kết quả xét nghiệm âm tính.", "location_found": "Bàn hóa trang", "related_character_name": "Scarlet Laurent", "is_key_evidence": False}
    ],
    "culprit_name": "Victor Moreau",
    "forensic_report": "Báo cáo pháp y:\n- Nhiệt độ tử thi 34.0°C lúc 01:00 phòng 24°C (tử vong khoảng 2 tiếng trước đó tức ~23:00).\n- Vết hằn tụ máu ngang cổ mỏng 1mm do dây mảnh siết gây ngạt thở."
  },
  {
    "title": "Bí Ẩn Chuyến Tàu Đêm Cổ Điển Orient",
    "summary": "Bá tước Gregory bị phát hiện tử vong tại toa hạng sang VIP 01 khi tàu đang vượt qua đèo núi mù sương.",
    "difficulty": "Medium",
    "victim": {
        "name": "Bá tước Gregory",
        "age": 58,
        "occupation": "Quý tộc & Quản lý mỏ than",
        "body_condition": "Tử thi ngồi tựa trên ghế nệm bọc nhung. Nhiệt độ tử thi 32.5°C đo lúc 03:00 sáng. Môi tím tái ngộ độc.",
        "location_found": "Toa VIP 01, Chuyến tàu Orient"
    },
    "suspects": [
        {
            "name": "Công nương Katherine",
            "age": 48,
            "occupation": "Vợ nạn nhân",
            "motive": "Phát hiện Bá tước chuẩn bị sang nhượng toàn bộ tài sản cho người tình.",
            "alibi": "Khai rằng ngủ tại toa VIP 02 từ 23:00 đêm đến sáng.",
            "persona": "Sang trọng, kiêu hãnh, luôn giữ vẻ lạnh lùng.",
            "is_culprit": True
        },
        {
            "name": "Thượng úy Marcus",
            "age": 36,
            "occupation": "Sĩ quan bảo vệ đoàn tàu",
            "motive": "Có mâu thuẫn nợ nần cờ bạc với nạn nhân.",
            "alibi": "Đi tuần dọc các toa tàu từ 00:00 đến 02:00.",
            "persona": "Cứng cỏi, kỷ luật nhưng có vết đen tài chính.",
            "is_culprit": False
        }
    ],
    "timeline": [
        {"event_time": "23:30", "description": "Bá tước uống ly rượu Brandy do Công nương Katherine rót sẵn.", "location": "Toa VIP 01", "character_name": "Gregory"},
        {"event_time": "00:15", "description": "Thuốc độc Cyanide bắt đầu phát huy tác dụng khiến nạn nhân ngạt thở tử vong.", "location": "Toa VIP 01", "character_name": "Katherine"}
    ],
    "evidences": [
        {"item_name": "Lọ nhẫn kim loại giấu ngăn thuốc", "description": "Lọ chứa dấu vết chất độc Cyanide dạng bột.", "location_found": "Trong bóp tay Công nương", "related_character_name": "Katherine", "is_key_evidence": True}
    ],
    "culprit_name": "Công nương Katherine",
    "forensic_report": "Báo cáo nghiệm tử thi:\n- Tử thi tử vong do ngộ độc Cyanide liều cao gây trụy hô hấp."
  }
]

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.LLM_API_BASE,
            api_key=settings.LLM_API_KEY
        )
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE

    def _build_prompt(self, theme: str, difficulty: str) -> str:
        return f"""Bạn là một chuyên gia sáng tác kịch bản game trinh thám giải đố kinh điển.
Hãy sáng tác một vụ án mạng trinh thám độc đáo với bối cảnh: "{theme}", độ khó: "{difficulty}".

YÊU CẦU BẮT BUỘC:
1. Báo cáo pháp y (body_condition & forensic_report) CHỈ ĐƯỢC CHỨA các dữ kiện vật lý/sinh học (nhiệt độ tử thi, độ hoen tử thi, trạng thái co cứng tử thi), TUYỆT ĐỐI KHÔNG GHI TRỰC TIẾP GIỜ CHẾT (Ví dụ: "Nạn nhân chết lúc 21:30" là SAI). Người chơi phải tự suy luận giờ chết dựa trên công thức giảm nhiệt độ tử thi (trung bình giảm 0.8 - 1°C mỗi giờ).
2. Danh sách nghi phạm phải có chính xác 1 hung thủ (is_culprit = true). Hung thủ phải có động cơ rõ ràng và một chứng cứ ngoại phạm (alibi) giả có lỗ hổng logic với dòng thời gian thực tế.
3. Trả về đúng định dạng JSON thuần khớp chính xác với JSON Schema sau:

{{
  "title": "Tên vụ án",
  "summary": "Tóm tắt bối cảnh vụ án",
  "difficulty": "{difficulty}",
  "victim": {{
    "name": "Tên nạn nhân",
    "age": 50,
    "occupation": "Nghề nghiệp",
    "body_condition": "Tình trạng tử thi (nhiệt độ tử thi, vết thương...)",
    "location_found": "Hiện trường"
  }},
  "suspects": [
    {{
      "name": "Tên nghi phạm 1",
      "age": 30,
      "occupation": "Nghề nghiệp",
      "motive": "Động cơ",
      "alibi": "Lời khai chứng cứ ngoại phạm",
      "persona": "Tính cách",
      "is_culprit": false
    }},
    {{
      "name": "Tên nghi phạm 2 (Hung thủ)",
      "age": 28,
      "occupation": "Nghề nghiệp",
      "motive": "Động cơ",
      "alibi": "Lời khai chứng cứ ngoại phạm giả",
      "persona": "Tính cách",
      "is_culprit": true
    }}
  ],
  "timeline": [
    {{
      "event_time": "21:00 - 21:30",
      "description": "Sự kiện xảy ra",
      "location": "Địa điểm",
      "character_name": "Tên nhân vật liên quan"
    }}
  ],
  "evidences": [
    {{
      "item_name": "Tên chứng cứ",
      "description": "Mô tả chứng cứ",
      "location_found": "Vị trí tìm thấy",
      "related_character_name": "Nhân vật liên quan",
      "is_key_evidence": true
    }}
  ],
  "culprit_name": "Tên hung thủ (trùng với tên nghi phạm is_culprit = true)",
  "forensic_report": "Báo cáo khám nghiệm pháp y chi tiết"
}}

TRẢ LỜI CHỈ BẰNG DỮ LIỆU JSON CHUẨN, KHÔNG CÓ LỜI DẪN HAY KHỐI CODE MARKDOWN.
"""

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
        reraise=False
    )
    def _call_9router_api(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": "You are a professional mystery game script generator. Reply ONLY with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content or ""

    def generate_case(self, theme: str = "Vụ án mạng tại biệt thự cổ", difficulty: str = "Medium") -> GeneratedCaseSchema:
        prompt = self._build_prompt(theme=theme, difficulty=difficulty)
        try:
            logger.info(f"Sending prompt to 9Router Proxy at {settings.LLM_API_BASE} (Model: {self.model})...")
            raw_response = self._call_9router_api(prompt)
            
            clean_json_str = raw_response.strip()
            if clean_json_str.startswith("```json"):
                clean_json_str = clean_json_str[7:]
            if clean_json_str.startswith("```"):
                clean_json_str = clean_json_str[3:]
            if clean_json_str.endswith("```"):
                clean_json_str = clean_json_str[:-3]
            clean_json_str = clean_json_str.strip()

            parsed_data = json.loads(clean_json_str)
            validated_case = GeneratedCaseSchema(**parsed_data)
            logger.info("Successfully generated and validated case from 9Router LLM!")
            return validated_case
        except Exception as e:
            logger.warning(f"Failed to generate case via 9Router LLM ({e}). Activating Dynamic Seed Case Pool fallback.")
            
            # CHỌN MỘT VỤ ÁN MẪU ĐÃ DẠNG MỖI LẦN CLICK
            selected_case = random.choice(DYNAMIC_SEED_CASES).copy()
            if theme and theme != "Vụ án mạng tại biệt thự cổ":
                selected_case["summary"] = f"Bối cảnh yêu cầu: '{theme}'. {selected_case['summary']}"
            selected_case["difficulty"] = difficulty
            
            return GeneratedCaseSchema(**selected_case)

llm_service = LLMService()
