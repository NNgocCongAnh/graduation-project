"""Unit tests for Client Integrity Middleware and HMAC-SHA256 verification."""

import time
import uuid
import hmac
import hashlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from security import ClientIntegrityMiddleware, CLIENT_SECRET

app = FastAPI()
app.add_middleware(ClientIntegrityMiddleware)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/case/sample")
def sample():
    return {"case_id": "case_test_001"}

@app.post("/api/case/generate")
def generate(payload: dict):
    return {"generated": payload}

client = TestClient(app)

def sign_request(method: str, path: str, body: bytes, secret: str = CLIENT_SECRET, ts_offset: float = 0):
    ts = str(int(time.time() + ts_offset))
    nonce = str(uuid.uuid4())
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = f"{method.upper()}\n{path}\n{ts}\n{nonce}\n{body_hash}"
    sig = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return {
        "X-Game-Client": "UnsolvedCaseFiles-v1",
        "X-Game-Timestamp": ts,
        "X-Game-Nonce": nonce,
        "X-Game-Signature": sig
    }

def test_public_health_check_allowed_without_auth():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_protected_endpoint_blocked_without_headers():
    res = client.get("/api/case/sample")
    assert res.status_code == 403
    assert "Access Denied" in res.json()["detail"]

def test_protected_endpoint_blocked_with_fake_signature():
    headers = {
        "X-Game-Client": "UnsolvedCaseFiles-v1",
        "X-Game-Timestamp": str(int(time.time())),
        "X-Game-Nonce": str(uuid.uuid4()),
        "X-Game-Signature": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    }
    res = client.get("/api/case/sample", headers=headers)
    assert res.status_code == 403
    assert "Invalid HMAC signature" in res.json()["detail"]

def test_protected_endpoint_success_with_valid_signature():
    path = "/api/case/sample"
    headers = sign_request("GET", path, b"")
    res = client.get(path, headers=headers)
    assert res.status_code == 200
    assert res.json()["case_id"] == "case_test_001"

def test_protected_post_endpoint_success_with_valid_signature():
    path = "/api/case/generate"
    body = b'{"country":"Viet Nam"}'
    headers = sign_request("POST", path, body)
    headers["Content-Type"] = "application/json"
    res = client.post(path, data=body, headers=headers)
    assert res.status_code == 200
    assert res.json()["generated"]["country"] == "Viet Nam"

def test_replay_attack_rejected():
    path = "/api/case/sample"
    headers = sign_request("GET", path, b"")
    # First request: should pass
    res1 = client.get(path, headers=headers)
    assert res1.status_code == 200
    # Replay identical request with identical nonce: must be rejected!
    res2 = client.get(path, headers=headers)
    assert res2.status_code == 403
    assert "Replay attack detected" in res2.json()["detail"]

def test_expired_timestamp_rejected():
    path = "/api/case/sample"
    # Timestamp from 5 minutes ago (> 60s)
    headers = sign_request("GET", path, b"", ts_offset=-300)
    res = client.get(path, headers=headers)
    assert res.status_code == 403
    assert "Request timestamp expired" in res.json()["detail"]


def test_rate_limiter_blocks_abuse():
    from security import reset_rate_limits, RATE_LIMIT_CASE_GEN_PER_MIN
    reset_rate_limits()
    path = "/api/case/generate"
    body = b'{"country":"Viet Nam"}'

    # Send requests up to the limit
    for _ in range(RATE_LIMIT_CASE_GEN_PER_MIN):
        headers = sign_request("POST", path, body)
        headers["Content-Type"] = "application/json"
        res = client.post(path, data=body, headers=headers)
        assert res.status_code == 200

    # Next request must be rejected with HTTP 429 Too Many Requests
    headers = sign_request("POST", path, body)
    headers["Content-Type"] = "application/json"
    blocked_res = client.post(path, data=body, headers=headers)
    assert blocked_res.status_code == 429
    assert "Rate limit exceeded" in blocked_res.json()["detail"]
    assert "Retry-After" in blocked_res.headers

    # Reset after test
    reset_rate_limits()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
