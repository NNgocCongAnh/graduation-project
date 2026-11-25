"""End-to-end integration tests for FastAPI Database persistence endpoints."""

import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import SessionLocal, DeductionRecord, CaseRecord
from security import sign_request

client = TestClient(app)


def test_get_sample_case_api():
    """Verify sample case endpoint serves properly and ensures persistence."""
    headers = sign_request("GET", "/api/case/sample")
    response = client.get("/api/case/sample", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-2026-001"
    assert "victim" in data
    assert "suspects" in data
    assert "evidences" in data


def test_query_cases_catalog():
    """Verify /api/cases query endpoint with pagination and structure."""
    path = "/api/cases?limit=5"
    headers = sign_request("GET", path)
    response = client.get(path, headers=headers)
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
    """Verify retrieving a specific case by its ID (client endpoint sanitizes ground_truth)."""
    headers = sign_request("GET", "/api/case/CASE-2026-001")
    response = client.get("/api/case/CASE-2026-001", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-2026-001"
    # Ground truth must be stripped from public client endpoint
    assert "ground_truth" not in data
    for susp in data["suspects"]:
        assert "is_culprit" not in susp
        assert "secret_innocent_fact" not in susp
    for ev in data["evidences"]:
        assert "is_crucial" not in ev
        assert "is_red_herring" not in ev

    # Internal endpoint retains full ground truth
    os.environ["INTERNAL_API_TOKEN"] = "test-internal-token"
    int_headers = sign_request("GET", "/api/case/CASE-2026-001/internal")
    int_headers["X-Internal-Token"] = "test-internal-token"
    internal_res = client.get("/api/case/CASE-2026-001/internal", headers=int_headers)
    assert internal_res.status_code == 200
    internal_data = internal_res.json()
    assert internal_data["ground_truth"]["culprit_id"] == "SUSP-01"


def test_verify_and_auto_logging_endpoint():
    """Verify that submitting a deduction calculates score and logs to DB."""
    # Submit a deduction to CASE-2026-001 with correct culprit and crucial clues
    payload = {
        "case_id": "CASE-2026-001",
        "selected_suspect_id": "SUSP-01",
        "selected_evidence_ids": ["EV-01", "EV-02"]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    headers = sign_request("POST", "/api/case/verify", body=raw_body)
    headers["Content-Type"] = "application/json"

    verify_res = client.post("/api/case/verify", content=raw_body, headers=headers)
    assert verify_res.status_code == 200
    res_data = verify_res.json()
    assert res_data["is_correct"] is True
    assert res_data["score"] == 100.0

    # Query statistics endpoint
    stats_headers = sign_request("GET", "/api/case/CASE-2026-001/stats")
    stats_res = client.get("/api/case/CASE-2026-001/stats", headers=stats_headers)
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
