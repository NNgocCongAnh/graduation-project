"""Unit tests for the SQLite Database Persistence Layer (database.py)."""

import os
import json
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    CaseDossier,
    VerifyRequest,
    VerifyResponse,
    DeductionVerdict,
    DeductionScoreBreakdown
)
from database import (
    Base,
    CaseRecord,
    DeductionRecord,
    save_case_to_db,
    get_case_from_db,
    list_cases_from_db,
    log_deduction_to_db,
    get_case_statistics,
    init_db
)
from llm_service import CaseGeneratorService


@pytest.fixture(scope="module")
def test_db():
    """Create an isolated in-memory SQLite database for testing."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_save_and_retrieve_case(test_db):
    """Test saving a sample case and retrieving it accurately from SQLite."""
    sample = CaseGeneratorService.get_sample_case()
    sample.case_id = "TEST-CASE-001"
    
    # Save to test DB
    record = save_case_to_db(sample, db=test_db, is_valid=True, validator_score=1.0)
    assert record.case_id == "TEST-CASE-001"
    assert record.culprit_id == sample.ground_truth.culprit_id
    assert record.suspects_count == len(sample.suspects)

    # Fetch back
    retrieved = get_case_from_db("TEST-CASE-001", db=test_db)
    assert retrieved is not None
    assert retrieved.case_id == "TEST-CASE-001"
    assert retrieved.title == sample.title
    assert retrieved.ground_truth.culprit_id == sample.ground_truth.culprit_id
    assert len(retrieved.suspects) == len(sample.suspects)
    assert len(retrieved.evidences) == len(sample.evidences)


def test_update_existing_case(test_db):
    """Test updating an already existing case in SQLite."""
    sample = CaseGeneratorService.get_sample_case()
    sample.case_id = "TEST-CASE-002"
    sample.title = "Original Title"
    save_case_to_db(sample, db=test_db)

    # Update title
    sample.title = "Updated Mystery Title"
    save_case_to_db(sample, db=test_db, validator_score=0.95)

    retrieved = get_case_from_db("TEST-CASE-002", db=test_db)
    assert retrieved is not None
    assert retrieved.title == "Updated Mystery Title"


def test_list_cases_filtering(test_db):
    """Test listing cases with limit, offset, and criteria filters."""
    cases = list_cases_from_db(db=test_db, limit=10)
    assert len(cases) >= 2
    case_ids = [c["case_id"] for c in cases]
    assert "TEST-CASE-001" in case_ids
    assert "TEST-CASE-002" in case_ids


def test_log_deductions_and_statistics(test_db):
    """Test logging multiple player attempts and calculating case difficulty telemetry."""
    case_id = "TEST-CASE-001"

    # Attempt 1: Perfect deduction
    req1 = VerifyRequest(
        case_id=case_id,
        selected_suspect_id="SUSPECT-02",
        selected_evidence_ids=["EVID-01", "EVID-04"]
    )
    res1 = VerifyResponse(
        case_id=case_id,
        is_correct=True,
        verdict=DeductionVerdict.SOLVED_PERFECT,
        culprit_identified=True,
        crucial_evidences_identified=True,
        found_crucial_count=2,
        total_crucial_count=2,
        score=100.0,
        feedback="Xuất sắc! Phá án hoàn hảo."
    )
    log_deduction_to_db(case_id, req1, res1, db=test_db, session_id="player-alpha")

    # Attempt 2: Wrong suspect accused
    req2 = VerifyRequest(
        case_id=case_id,
        selected_suspect_id="SUSPECT-01",
        selected_evidence_ids=["EVID-02"]
    )
    res2 = VerifyResponse(
        case_id=case_id,
        is_correct=False,
        verdict=DeductionVerdict.WRONG_SUSPECT,
        culprit_identified=False,
        crucial_evidences_identified=False,
        found_crucial_count=0,
        total_crucial_count=2,
        score=0.0,
        feedback="Sai đối tượng! Nghi phạm có alibi vững chắc."
    )
    log_deduction_to_db(case_id, req2, res2, db=test_db, session_id="player-beta")

    # Attempt 3: Trapped by red herring
    req3 = VerifyRequest(
        case_id=case_id,
        selected_suspect_id="SUSPECT-03",
        selected_evidence_ids=["EVID-03"]
    )
    res3 = VerifyResponse(
        case_id=case_id,
        is_correct=False,
        verdict=DeductionVerdict.TRAPPED_BY_RED_HERRING,
        culprit_identified=False,
        crucial_evidences_identified=False,
        red_herrings_selected_count=1,
        score=15.0,
        feedback="Bị đánh lừa bởi manh mối giả."
    )
    log_deduction_to_db(case_id, req3, res3, db=test_db, session_id="player-gamma")

    # Compute stats
    stats = get_case_statistics(case_id, db=test_db)
    assert stats["case_id"] == case_id
    assert stats["total_attempts"] == 3
    assert stats["solved_count"] == 1
    assert stats["solve_rate_percentage"] == round((1 / 3) * 100.0, 2)
    assert stats["average_score"] == round((100.0 + 0.0 + 15.0) / 3, 2)
    assert stats["accused_frequency"]["SUSPECT-02"] == 1
    assert stats["accused_frequency"]["SUSPECT-01"] == 1
    assert stats["accused_frequency"]["SUSPECT-03"] == 1
    assert stats["common_verdicts"][DeductionVerdict.SOLVED_PERFECT.value] == 1
