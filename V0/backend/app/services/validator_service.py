import logging
from typing import List, Tuple, Dict, Any
from app.schemas.case_schema import GeneratedCaseSchema

logger = logging.getLogger(__name__)

class CaseValidatorService:
    """
    Module Validator kiểm tra luật logic (Rule-based Consistency Checking).
    Đảm bảo dữ liệu vụ án không vi phạm các quy tắc cứng cốt lõi.
    """
    
    def validate_case_schema(self, case_data: GeneratedCaseSchema) -> Tuple[bool, List[str]]:
        """
        Kiểm tra tính nhất quán logic của đối tượng GeneratedCaseSchema.
        Trả về (is_valid: bool, errors: List[str])
        """
        errors: List[str] = []

        # 1. Kiểm tra sự tồn tại của Nạn nhân
        if not case_data.victim or not case_data.victim.name:
            errors.append("Hồ sơ vụ án thiếu thông tin nạn nhân.")

        # 2. Kiểm tra số lượng nghi phạm (Ít nhất 2 nghi phạm)
        if not case_data.suspects or len(case_data.suspects) < 2:
            errors.append("Vụ án phải có ít nhất 2 nghi phạm.")

        # 3. Kiểm tra số lượng hung thủ (Phải có đúng 1 hung thủ is_culprit = True)
        culprit_suspects = [s for s in case_data.suspects if s.is_culprit]
        if len(culprit_suspects) == 0:
            errors.append("Không tìm thấy nghi phạm nào được gắn cờ là hung thủ (is_culprit = true).")
        elif len(culprit_suspects) > 1:
            errors.append(f"Có nhiều hơn 1 hung thủ trong danh sách nghi phạm: {[s.name for s in culprit_suspects]}.")

        # 4. Kiểm tra tên hung thủ chính xác hoặc khớp linh hoạt với nghi phạm
        culprit_str = case_data.culprit_name.strip().lower()
        matched_culprit = next(
            (s for s in case_data.suspects if s.name.strip().lower() == culprit_str or culprit_str in s.name.strip().lower() or s.name.strip().lower() in culprit_str), 
            None
        )
        if not matched_culprit:
            errors.append(f"Tên hung thủ '{case_data.culprit_name}' không trùng khớp với bất kỳ nghi phạm nào trong danh sách.")
        elif not matched_culprit.is_culprit:
            errors.append(f"Tên hung thủ '{case_data.culprit_name}' chưa được đánh dấu cờ is_culprit = true.")

        # 5. Kiểm tra dòng thời gian Timeline
        if not case_data.timeline or len(case_data.timeline) < 2:
            errors.append("Dòng thời gian vụ án phải có ít nhất 2 mốc sự kiện.")

        # 6. Kiểm tra chứng cứ hiện trường & Chứng cứ mấu chốt
        if not case_data.evidences or len(case_data.evidences) == 0:
            errors.append("Vụ án không có chứng cứ hiện trường nào.")
        
        key_evidences = [e for e in case_data.evidences if e.is_key_evidence]
        if len(key_evidences) == 0:
            errors.append("Cần có ít nhất 1 chứng cứ mấu chốt (is_key_evidence = true) để phục vụ suy luận phá án.")

        is_valid = len(errors) == 0
        if is_valid:
            logger.info("Case validation passed successfully with 0 logic errors.")
        else:
            logger.warning(f"Case validation failed with {len(errors)} errors: {errors}")

        return is_valid, errors

validator_service = CaseValidatorService()
