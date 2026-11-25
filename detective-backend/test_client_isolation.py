"""Unit & Integration Tests for Client Schema Isolation and Fail-Closed Validation (B2).

Verifies:
1. Public client endpoints (/api/case/sample, /api/case/{case_id}, /api/case/generate)
   NEVER leak ground_truth, is_culprit, secret_innocent_fact, is_crucial, or is_red_herring.
2. Internal endpoint (/api/case/{case_id}/internal) retains complete ground truth.
3. Cases that fail validation are recorded with is_valid=False in SQLite and rejected with HTTP 422.
4. Server-authoritative deduction verification (/api/case/verify) scores free-text reasoning.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))

import json
from main import app, save_case_persistent
from models import CaseDossier, Victim, Suspect, Evidence, GroundTruth, ForensicData, GenerationMetadata
from database import get_case_from_db, list_cases_from_db
from security import sign_request

client = TestClient(app)
TEST_INTERNAL_TOKEN = "test-internal-token"


def test_sample_case_client_isolation():
    """Verify GET /api/case/sample strips all spoilers and secret cheat flags."""
    headers = sign_request("GET", "/api/case/sample")
    res = client.get("/api/case/sample", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Core structure present
    assert data["case_id"] == "CASE-2026-001"
    assert "title" in data
    assert "summary" in data
    assert "victim" in data
    assert len(data["suspects"]) >= 2
    assert len(data["evidences"]) >= 2

    # Secret Ground Truth must NOT be present
    assert "ground_truth" not in data, "CRITICAL: ground_truth leaked in /api/case/sample"
    assert "reasoning_chain" not in data, "CRITICAL: reasoning_chain leaked in /api/case/sample"

    # Suspect cheat flags must NOT be present
    for s in data["suspects"]:
        assert "is_culprit" not in s, f"CRITICAL: is_culprit leaked for suspect {s.get('id')}"
        assert "secret_innocent_fact" not in s, f"CRITICAL: secret_innocent_fact leaked for suspect {s.get('id')}"

    # Evidence cheat flags must NOT be present
    for e in data["evidences"]:
        assert "is_crucial" not in e, f"CRITICAL: is_crucial leaked for evidence {e.get('id')}"
        assert "is_red_herring" not in e, f"CRITICAL: is_red_herring leaked for evidence {e.get('id')}"
        assert "linked_suspect_id" not in e, f"CRITICAL: linked_suspect_id leaked for evidence {e.get('id')}"
        assert "is_weapon" not in e, f"CRITICAL: is_weapon (murder weapon flag) leaked for evidence {e.get('id')}"


def test_get_case_by_id_client_isolation():
    """Verify GET /api/case/{case_id} strips spoilers while internal endpoint preserves them."""
    case_id = "CASE-2026-001"

    # 1. Public client endpoint
    headers = sign_request("GET", f"/api/case/{case_id}")
    pub_res = client.get(f"/api/case/{case_id}", headers=headers)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()

    assert "ground_truth" not in pub_data
    assert "reasoning_chain" not in pub_data
    for s in pub_data["suspects"]:
        assert "is_culprit" not in s
        assert "secret_innocent_fact" not in s
    for e in pub_data["evidences"]:
        assert "is_crucial" not in e
        assert "is_red_herring" not in e

    # 2. Internal endpoint for benchmark runner / evaluation (requires server-side token)
    os.environ["INTERNAL_API_TOKEN"] = TEST_INTERNAL_TOKEN
    int_headers = sign_request("GET", f"/api/case/{case_id}/internal")
    int_headers["X-Internal-Token"] = TEST_INTERNAL_TOKEN
    int_res = client.get(f"/api/case/{case_id}/internal", headers=int_headers)
    assert int_res.status_code == 200
    int_data = int_res.json()

    assert "ground_truth" in int_data
    assert int_data["ground_truth"]["culprit_id"] == "SUSP-01"
    assert "core_contradiction" in int_data["ground_truth"]
    assert any(s.get("is_culprit") for s in int_data["suspects"])


def test_database_records_is_valid_accurately():
    """Verify SQLite database records is_valid=False and validator_score for invalid cases."""
    invalid_case = CaseDossier(
        case_id="CASE-TEST-INVALID-01",
        title="Vụ án kiểm thử không hợp lệ",
        summary="Vụ án dùng để kiểm tra việc lưu cờ is_valid=False vào cơ sở dữ liệu SQLite.",
        victim=Victim(
            name="Nạn nhân Test",
            age=40,
            occupation="Thương gia",
            forensic_data=ForensicData(
                ambient_temp=20.0,
                body_temp=28.0,
                livor_mortis_state="Cố định",
                wound_description="Vết thương thử nghiệm",
                estimated_tod_start="14:00",
                estimated_tod_end="16:00"
            )
        ),
        suspects=[
            Suspect(
                id="SUSP-01",
                name="Nghi phạm 1",
                age=35,
                occupation="Kế toán",
                motive="Tiền",
                alibi_start="10:00",
                alibi_end="12:00",
                alibi_statement="Tôi ở nhà",
                is_culprit=True
            ),
            Suspect(
                id="SUSP-02",
                name="Nghi phạm 2",
                age=30,
                occupation="Lái xe",
                motive="Thù tức",
                alibi_start="14:00",
                alibi_end="16:00",
                alibi_statement="Tôi đang lái xe",
                is_culprit=False
            )
        ],
        evidences=[
            Evidence(
                id="EV-01",
                title="Dao rỉ sét",
                location="Bụi cây",
                description="Hung khí gây án",
                is_crucial=False,
                is_red_herring=False
            ),
            Evidence(
                id="EV-02",
                title="Găng tay",
                location="Thùng rác",
                description="Vật chứng phụ",
                is_crucial=False,
                is_red_herring=False
            )
        ],
        ground_truth=GroundTruth(
            culprit_id="SUSP-01",
            actual_crime_time="23:30",  # Outside TOD window 14:00-16:00
            murder_weapon="Dao rỉ sét",
            core_contradiction="Mâu thuẫn kiểm thử"
        ),
        metadata=GenerationMetadata(
            model_name="test-model",
            validator_score=0.5
        )
    )

    # Persist with explicit invalid status
    save_case_persistent(invalid_case, is_valid=False, validator_score=0.5)

    # Verify directly from SQLite ORM table
    from database import SessionLocal, CaseRecord
    from sqlalchemy import select

    with SessionLocal() as db:
        record = db.execute(select(CaseRecord).where(CaseRecord.case_id == "CASE-TEST-INVALID-01")).scalar_one_or_none()
        assert record is not None
        assert record.is_valid is False, "DB record must store is_valid=False"
        assert record.validator_score == 0.5, "DB record must store validator_score=0.5"


def test_verify_endpoint_supports_free_text_reasoning():
    """Verify POST /api/case/verify evaluates free-text deductive reasoning without client cheat flags."""
    # Accuse true killer SUSP-01 with detailed reasoning text
    req_payload = {
        "case_id": "CASE-2026-001",
        "selected_suspect_id": "SUSP-01",
        "selected_evidence_ids": [],
        "reasoning": "Dựa trên báo cáo pháp y Henssge, thời gian tử vong thực tế là từ 22:30 đến 23:30. Ngoại phạm của bác sĩ Julian Grey mâu thuẫn hoàn toàn với bếp lò than nguội ngắt và ấm trà khô. Hung khí là dao rạch thư bạc giấu trong ống khói."
    }

    raw_body = json.dumps(req_payload).encode("utf-8")
    headers = sign_request("POST", "/api/case/verify", body=raw_body)
    headers["Content-Type"] = "application/json"

    res = client.post("/api/case/verify", content=raw_body, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == "CASE-2026-001"
    assert data["culprit_identified"] is True
    assert data["is_correct"] is True
    assert data["score"] >= 70.0
    assert "Henssge" in data["feedback"] or "ngoại phạm" in data["feedback"]
    assert data["core_contradiction"] is not None


def test_internal_endpoints_reject_game_client_signature_only(monkeypatch):
    """A valid game-client HMAC signature (extractable from the client) must NOT unlock ground truth."""
    case_id = "CASE-2026-001"
    for path in (f"/api/case/{case_id}/internal", f"/api/case/{case_id}/graph"):
        monkeypatch.delenv("INTERNAL_API_TOKEN", raising=False)
        res = client.get(path, headers=sign_request("GET", path))
        assert res.status_code == 403, f"{path} must be disabled when INTERNAL_API_TOKEN is unset"

        monkeypatch.setenv("INTERNAL_API_TOKEN", TEST_INTERNAL_TOKEN)
        res = client.get(path, headers=sign_request("GET", path))
        assert res.status_code == 403, f"{path} must require X-Internal-Token"

        headers = sign_request("GET", path)
        headers["X-Internal-Token"] = "wrong-token"
        assert client.get(path, headers=headers).status_code == 403

        headers = sign_request("GET", path)
        headers["X-Internal-Token"] = TEST_INTERNAL_TOKEN
        assert client.get(path, headers=headers).status_code == 200


def test_case_listings_do_not_leak_culprit_id():
    """Lobby listings (/api/case/all, /api/cases) must not expose culprit_id."""
    for path in ("/api/case/all", "/api/cases"):
        res = client.get(path, headers=sign_request("GET", path))
        assert res.status_code == 200
        body = res.json()
        items = body.get("cases", body.get("items", []))
        assert items, f"{path} returned no cases"
        for item in items:
            assert "culprit_id" not in item, f"CRITICAL: culprit_id leaked in {path}"
