import sys
import os
import pytest

# Thêm thư mục backend vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models.models import Case, Character, TimelineEvent, Evidence
from app.services.llm_service import llm_service
from app.services.validator_service import validator_service

def test_database_creation():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        case_count = db.query(Case).count()
        assert case_count >= 0
    finally:
        db.close()

def test_mock_seed_case_generation_and_validation():
    # Test sinh case và kiêm tra validator
    case_schema = llm_service.generate_case(theme="Vụ án biệt thự", difficulty="Medium")
    assert case_schema.title is not None
    assert case_schema.victim.name is not None
    assert len(case_schema.suspects) >= 2
    
    is_valid, errors = validator_service.validate_case_schema(case_schema)
    assert is_valid is True
    assert len(errors) == 0

def test_circular_fk_case_character():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        new_case = Case(title="Test Circular FK Case", status="generating")
        db.add(new_case)
        db.commit()
        db.refresh(new_case)

        suspect = Character(
            case_id=new_case.id,
            name="Nghi phạm Test",
            role="suspect",
            is_culprit=True
        )
        db.add(suspect)
        db.commit()
        db.refresh(suspect)

        # Cập nhật culprit_id sau khi đã chèn suspect
        new_case.culprit_id = suspect.id
        new_case.status = "ready"
        db.commit()

        fetched = db.query(Case).filter(Case.id == new_case.id).first()
        assert fetched.culprit_id == suspect.id
        assert fetched.culprit.name == "Nghi phạm Test"

        # Clean up
        db.delete(new_case)
        db.commit()
    finally:
        db.close()
