"""End-to-end integration tests for FastAPI Database persistence endpoints."""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))

from main import app
from database import SessionLocal, DeductionRecord, CaseRecord

client = TestClient(app)


def test_get_sample_case_api():
    """Verify sample case endpoint serves properly and ensures persistence."""
    response = client.get("/api/case/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-2026-001"
    assert "victim" in data
    assert "suspects" in data
    assert "evidences" in data


def test_query_cases_catalog():
    """Verify /api/cases query endpoint with pagination and structure."""
    response = client.get("/api/cases?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 1
    assert len(data["items"]) <= 5
    first_item = data["items"][0]
    assert "case_id" in first_item
    assert "title" in first_item


def test_get_case_by_id_endpoint():
    """Verify retrieving a specific case by its ID."""
    response = client.get("/api/case/CASE-2026-001")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-2026-001"
    assert data["ground_truth"]["culprit_id"] == "SUSP-01"


def test_verify_and_auto_logging_endpoint():
    """Verify that submitting a deduction calculates score and logs to DB."""
    # Submit a deduction to CASE-2026-001 with correct culprit and crucial clues
    payload = {
        "case_id": "CASE-2026-001",
        "selected_suspect_id": "SUSP-01",
        "selected_evidence_ids": ["EV-01", "EV-02"]
    }
    verify_res = client.post("/api/case/verify", json=payload)
    assert verify_res.status_code == 200
    res_data = verify_res.json()
    assert res_data["is_correct"] is True
    assert res_data["score"] == 100.0

    # Query statistics endpoint
    stats_res = client.get("/api/case/CASE-2026-001/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["case_id"] == "CASE-2026-001"
    assert stats_data["total_attempts"] >= 1
    assert stats_data["solved_count"] >= 1
    assert stats_data["solve_rate_percentage"] > 0.0

    # Verify directly from DB session
    with SessionLocal() as db:
        logs = db.query(DeductionRecord).filter(DeductionRecord.case_id == "CASE-2026-001").all()
        assert len(logs) >= 1
        latest = logs[-1]
        assert latest.accused_id == "SUSP-01"
        assert latest.is_correct is True
        assert latest.score == 100.0
