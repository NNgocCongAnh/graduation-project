from typing import List, Optional
from pydantic import BaseModel, Field

class VictimSchema(BaseModel):
    name: str = Field(..., description="Tên nạn nhân")
    age: int = Field(..., description="Tuổi của nạn nhân")
    occupation: str = Field(..., description="Nghề nghiệp của nạn nhân")
    body_condition: str = Field(
        ..., 
        description="Báo cáo tình trạng tử thi (nhiệt độ, độ hoen tử thi, dấu vết... KHÔNG ghi trực tiếp giờ chết)"
    )
    location_found: str = Field(..., description="Vị trí phát hiện thi thể")

class SuspectSchema(BaseModel):
    name: str = Field(..., description="Tên nghi phạm")
    age: int = Field(..., description="Tuổi nghi phạm")
    occupation: str = Field(..., description="Nghề nghiệp nghi phạm")
    motive: str = Field(..., description="Động cơ nghi vấn gây án")
    alibi: str = Field(..., description="Lời khai chứng cứ ngoại phạm kèm mốc thời gian")
    persona: str = Field(..., description="Tính cách và tiểu sử sơ bộ")
    is_culprit: bool = Field(False, description="Đánh dấu đây có phải là hung thủ thực sự hay không")

class TimelineEventSchema(BaseModel):
    event_time: str = Field(..., description="Mốc thời gian diễn ra (VD: 21:15 - 21:30)")
    description: str = Field(..., description="Mô tả sự kiện diễn ra")
    location: Optional[str] = Field(None, description="Địa điểm diễn ra sự kiện")
    character_name: Optional[str] = Field(None, description="Nhân vật chính liên quan đến sự kiện")

class EvidenceSchema(BaseModel):
    item_name: str = Field(..., description="Tên vật chứng")
    description: str = Field(..., description="Mô tả chi tiết vật chứng")
    location_found: Optional[str] = Field(None, description="Vị trí tìm thấy vật chứng")
    related_character_name: Optional[str] = Field(None, description="Tên nhân vật liên quan đến vật chứng")
    is_key_evidence: bool = Field(False, description="Vật chứng mấu chốt để chỉ danh hung thủ")

class GeneratedCaseSchema(BaseModel):
    """
    Schema tổng hợp kết quả sinh vụ án từ LLM Pipeline (Structured Output)
    """
    title: str = Field(..., description="Tiêu đề vụ án")
    summary: str = Field(..., description="Tóm tắt bối cảnh vụ án")
    difficulty: str = Field("Medium", description="Độ khó vụ án (Easy, Medium, Hard)")
    victim: VictimSchema = Field(..., description="Thông tin nạn nhân")
    suspects: List[SuspectSchema] = Field(..., description="Danh sách các nghi phạm (bao gồm hung thủ)")
    timeline: List[TimelineEventSchema] = Field(..., description="Dòng thời gian các sự kiện liên quan")
    evidences: List[EvidenceSchema] = Field(..., description="Danh sách chứng cứ hiện trường")
    culprit_name: str = Field(..., description="Tên hung thủ chính xác")
    forensic_report: str = Field(..., description="Báo cáo khám nghiệm pháp y chi tiết (ẩn giờ chết)")
