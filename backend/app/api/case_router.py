import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Case, Character, TimelineEvent, Evidence
from app.services.llm_service import llm_service
from app.services.validator_service import validator_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cases", tags=["cases"])

# --- Request & Response Schemas ---
class GenerateCaseRequest(BaseModel):
    theme: str = "Vụ án mạng tại biệt thự cổ"
    difficulty: str = "Medium"

class GuessRequest(BaseModel):
    suspect_id: int
    reasoning: Optional[str] = None

class GuessResponse(BaseModel):
    is_correct: bool
    message: str
    actual_culprit_name: str

# --- Background Task Helper ---
def background_generate_case_task(case_id: int, theme: str, difficulty: str):
    """
    Hàm xử lý sinh vụ án trong BackgroundTasks để tránh HTTP Timeout.
    """
    # Khởi tạo DB session riêng cho background worker
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        db_case = db.query(Case).filter(Case.id == case_id).first()
        if not db_case:
            logger.error(f"Case ID {case_id} not found in background task.")
            return

        logger.info(f"Starting background generation for Case ID {case_id}...")
        
        # 1. Gọi LLM Service qua 9Router Gateway (có Tenacity retry & Fallback Mock)
        generated_data = llm_service.generate_case(theme=theme, difficulty=difficulty)
        
        # 2. Gọi Validator Service kiểm tra nhất quán logic
        is_valid, validation_errors = validator_service.validate_case_schema(generated_data)
        if not is_valid:
            logger.warning(f"Case ID {case_id} failed validation, proceeding with fallback correction...")

        # 3. Cập nhật thông tin Case
        db_case.title = generated_data.title
        db_case.summary = generated_data.summary
        db_case.difficulty = generated_data.difficulty
        db_case.forensic_report = generated_data.forensic_report
        db.flush()

        # 4. Lưu Nạn nhân (Victim) vào bảng Character
        victim_char = Character(
            case_id=db_case.id,
            name=generated_data.victim.name,
            age=generated_data.victim.age,
            role="victim",
            occupation=generated_data.victim.occupation,
            motive=None,
            alibi=None,
            persona=f"Tình trạng tử thi: {generated_data.victim.body_condition}",
            is_culprit=False
        )
        db.add(victim_char)
        db.flush()

        # 5. Lưu Nghi phạm (Suspects) và tìm Hung thủ
        culprit_char_obj = None
        for s in generated_data.suspects:
            char_obj = Character(
                case_id=db_case.id,
                name=s.name,
                age=s.age,
                role="suspect",
                occupation=s.occupation,
                motive=s.motive,
                alibi=s.alibi,
                persona=s.persona,
                is_culprit=s.is_culprit
            )
            db.add(char_obj)
            db.flush()
            
            if s.is_culprit or s.name.strip().lower() == generated_data.culprit_name.strip().lower():
                culprit_char_obj = char_obj

        # 6. GIẢI QUYẾT CIRCULAR FK: Update culprit_id sau khi Character đã có ID
        if culprit_char_obj:
            db_case.culprit_id = culprit_char_obj.id

        # 7. Lưu Dòng thời gian (Timeline)
        for t in generated_data.timeline:
            # Tìm character_id liên quan nếu tên khớp
            rel_char = db.query(Character).filter(Character.case_id == db_case.id, Character.name == t.character_name).first()
            event_obj = TimelineEvent(
                case_id=db_case.id,
                event_time=t.event_time,
                description=t.description,
                location=t.location,
                character_id=rel_char.id if rel_char else None
            )
            db.add(event_obj)

        # 8. Lưu Chứng cứ hiện trường (Evidence)
        for e in generated_data.evidences:
            rel_char = db.query(Character).filter(Character.case_id == db_case.id, Character.name == e.related_character_name).first()
            evidence_obj = Evidence(
                case_id=db_case.id,
                item_name=e.item_name,
                description=e.description,
                location_found=e.location_found,
                related_character_id=rel_char.id if rel_char else None,
                is_key_evidence=e.is_key_evidence
            )
            db.add(evidence_obj)

        # 9. Đổi trạng thái Case thành 'ready'
        db_case.status = "ready"
        db.commit()
        logger.info(f"Case ID {case_id} generation successfully completed and status set to 'ready'!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error in background generation task for Case ID {case_id}: {e}")
        db_case = db.query(Case).filter(Case.id == case_id).first()
        if db_case:
            db_case.status = "failed"
            db.commit()
    finally:
        db.close()


# --- API Routes ---

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def trigger_generate_case(
    payload: GenerateCaseRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Kích hoạt sinh vụ án mới bất đồng bộ (Async BackgroundTask).
    Trả về ngay trạng thái 'generating' kèm case_id để Frontend thực hiện Polling.
    """
    new_case = Case(
        title=f"Đang sinh vụ án ({payload.theme})...",
        summary="Dữ liệu vụ án đang được AI tạo qua 9Router Gateway...",
        difficulty=payload.difficulty,
        status="generating",
        culprit_id=None
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    # Đưa tác vụ gọi LLM vào BackgroundTasks
    background_tasks.add_task(
        background_generate_case_task, 
        case_id=new_case.id, 
        theme=payload.theme, 
        difficulty=payload.difficulty
    )

    return {
        "case_id": new_case.id,
        "status": "generating",
        "message": "Vụ án đang được AI tạo bất đồng bộ. Vui lòng polling trạng thái qua GET /api/cases/{case_id}."
    }

@router.get("")
def list_cases(db: Session = Depends(get_db)):
    """
    Lấy danh sách tất cả các vụ án.
    """
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "summary": c.summary,
            "difficulty": c.difficulty,
            "status": c.status,
            "created_at": c.created_at
        }
        for c in cases
    ]

@router.get("/{case_id}")
def get_case_detail(case_id: int, db: Session = Depends(get_db)):
    """
    Lấy toàn bộ hồ sơ vụ án chi tiết (Cho phép Frontend polling kiểm tra trạng thái status).
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Không tìm thấy vụ án.")

    if case.status == "generating":
        return {
            "id": case.id,
            "status": "generating",
            "message": "Vụ án vẫn đang được AI tiếp tục tạo..."
        }

    if case.status == "failed":
        return {
            "id": case.id,
            "status": "failed",
            "message": "Quá trình sinh vụ án thất bại."
        }

    # Format dữ liệu vụ án hoàn chỉnh khi status == "ready"
    victim = db.query(Character).filter(Character.case_id == case.id, Character.role == "victim").first()
    suspects = db.query(Character).filter(Character.case_id == case.id, Character.role == "suspect").all()
    timeline = db.query(TimelineEvent).filter(TimelineEvent.case_id == case.id).order_by(TimelineEvent.id.asc()).all()
    evidences = db.query(Evidence).filter(Evidence.case_id == case.id).all()

    return {
        "id": case.id,
        "title": case.title,
        "summary": case.summary,
        "difficulty": case.difficulty,
        "status": case.status,
        "forensic_report": case.forensic_report,
        "victim": {
            "id": victim.id,
            "name": victim.name,
            "age": victim.age,
            "occupation": victim.occupation,
            "persona": victim.persona
        } if victim else None,
        "suspects": [
            {
                "id": s.id,
                "name": s.name,
                "age": s.age,
                "occupation": s.occupation,
                "motive": s.motive,
                "alibi": s.alibi,
                "persona": s.persona
            }
            for s in suspects
        ],
        "timeline": [
            {
                "id": t.id,
                "event_time": t.event_time,
                "description": t.description,
                "location": t.location
            }
            for t in timeline
        ],
        "evidences": [
            {
                "id": e.id,
                "item_name": e.item_name,
                "description": e.description,
                "location_found": e.location_found,
                "is_key_evidence": e.is_key_evidence
            }
            for e in evidences
        ]
    }

@router.post("/{case_id}/guess", response_model=GuessResponse)
def guess_culprit(case_id: int, payload: GuessRequest, db: Session = Depends(get_db)):
    """
    Xác nhận lựa chọn hung thủ của người chơi.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Không tìm thấy vụ án.")

    if not case.culprit_id:
        raise HTTPException(status_code=400, detail="Vụ án chưa hoàn tất dữ liệu hung thủ.")

    guessed_suspect = db.query(Character).filter(Character.id == payload.suspect_id, Character.case_id == case.id).first()
    if not guessed_suspect:
        raise HTTPException(status_code=404, detail="Nghi phạm không hợp lệ trong vụ án này.")

    actual_culprit = db.query(Character).filter(Character.id == case.culprit_id).first()
    actual_culprit_name = actual_culprit.name if actual_culprit else "Không xác định"

    is_correct = (guessed_suspect.id == case.culprit_id)
    if is_correct:
        msg = f"CHÍNH XÁC! Bạn đã phá án thành công. {guessed_suspect.name} chính là hung thủ thực sự."
    else:
        msg = f"RẤT TIẾC! Lời buộc tội của bạn đã sai. {guessed_suspect.name} không phải hung thủ."

    return GuessResponse(
        is_correct=is_correct,
        message=msg,
        actual_culprit_name=actual_culprit_name
    )
