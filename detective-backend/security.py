"""Client Integrity and Request Signing Security Module.

Implements HMAC-SHA256 request authentication and replay prevention.
Protects the AI Detective Backend against unauthorized scraping, curl/Postman
exploitation, and denial-of-service token drain when hosted publicly on Cloud.

Security Model:
1. Shared Secret: Obfuscated at the byte-level inside the Unity standalone binary.
2. Canonical Request: Method + Path + Timestamp + Nonce + SHA256(Body).
3. Sliding Window & Anti-Replay: 60-second validity window + unique nonce tracking.
"""

import os
import time
import hmac
import hashlib
import logging
from typing import Tuple, Dict
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Load environment configuration
load_dotenv()

logger = logging.getLogger("security")

# Configuration of shared HMAC secret and signature requirement
# Never hardcode production secrets in source code; enforce strict environment configuration
CLIENT_SECRET = os.getenv("GAME_CLIENT_SECRET", "").strip()
REQUIRE_SIGNATURE = os.getenv("REQUIRE_CLIENT_SIGNATURE", "true").lower() in ("true", "1", "yes")

# Fail-closed policy: Refuse to start if signature verification is required but no secret is configured
if not CLIENT_SECRET:
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"):
        CLIENT_SECRET = "test_temporary_hmac_secret_for_unit_tests_only"
    elif REQUIRE_SIGNATURE:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: 'GAME_CLIENT_SECRET' environment variable is missing or empty. "
            "The system enforces request integrity verification and will not start with an unconfigured secret. "
            "Please specify GAME_CLIENT_SECRET in your environment or .env file."
        )

# Max allowed time drift between client and server (in seconds)
MAX_TIME_DRIFT = 60.0

# In-memory sliding window nonce cache: nonce -> timestamp
_SEEN_NONCES: Dict[str, float] = {}

# Rate Limiting configuration for expensive generative endpoints
RATE_LIMIT_CASE_GEN_PER_MIN = int(os.getenv("RATE_LIMIT_CASE_GEN_PER_MIN", "5"))
_RATE_LIMIT_STORE: Dict[str, list] = {}


def check_rate_limit(client_identifier: str, limit: int = RATE_LIMIT_CASE_GEN_PER_MIN, window_seconds: float = 60.0) -> Tuple[bool, int]:
    """Check if client identifier exceeds the sliding window rate limit.

    Returns (allowed: bool, retry_after_seconds: int)
    """
    now = time.time()
    timestamps = _RATE_LIMIT_STORE.get(client_identifier, [])
    valid_timestamps = [ts for ts in timestamps if now - ts < window_seconds]

    if len(valid_timestamps) >= limit:
        oldest_ts = valid_timestamps[0]
        retry_after = max(1, int(window_seconds - (now - oldest_ts)))
        _RATE_LIMIT_STORE[client_identifier] = valid_timestamps
        return False, retry_after

    valid_timestamps.append(now)
    _RATE_LIMIT_STORE[client_identifier] = valid_timestamps
    return True, 0


def reset_rate_limits() -> None:
    """Clear all rate limit tracking entries (for unit tests)."""
    _RATE_LIMIT_STORE.clear()


def _clean_expired_nonces(current_time: float) -> None:
    """Remove nonces older than 2x the time drift window."""
    expired = [n for n, ts in _SEEN_NONCES.items() if current_time - ts > MAX_TIME_DRIFT * 2]
    for n in expired:
        del _SEEN_NONCES[n]


def verify_signature(
    method: str,
    path: str,
    client_id: str,
    timestamp_str: str,
    nonce: str,
    signature: str,
    body_bytes: bytes
) -> Tuple[bool, str]:
    """Verify HMAC-SHA256 signature and anti-replay constraints.

    Returns:
        (is_valid, error_reason)
    """
    if not REQUIRE_SIGNATURE:
        return True, "Signature requirement disabled"

    if not client_id or not client_id.startswith("UnsolvedCaseFiles"):
        return False, "Invalid or missing X-Game-Client header"

    if not timestamp_str or not nonce or not signature:
        return False, "Missing security headers (Timestamp, Nonce, or Signature)"

    try:
        req_time = float(timestamp_str)
    except ValueError:
        return False, "Invalid timestamp format (must be unix epoch seconds)"

    now = time.time()
    if abs(now - req_time) > MAX_TIME_DRIFT:
        return False, f"Request timestamp expired (drift: {abs(now - req_time):.1f}s, max allowed: {MAX_TIME_DRIFT}s)"

    # Clean up and check nonce replay
    _clean_expired_nonces(now)
    if nonce in _SEEN_NONCES:
        return False, "Replay attack detected: Nonce has already been processed"

    # Compute body hash
    body_hash = hashlib.sha256(body_bytes if body_bytes else b"").hexdigest()

    # Canonical string to sign
    canonical = f"{method.upper()}\n{path}\n{timestamp_str}\n{nonce}\n{body_hash}"

    # Compute expected HMAC-SHA256
    expected_sig = hmac.new(
        CLIENT_SECRET.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    if not hmac.compare_digest(signature.lower(), expected_sig.lower()):
        return False, "Invalid HMAC signature (shared secret mismatch)"

    # Record nonce
    _SEEN_NONCES[nonce] = now
    return True, "Valid"


def sign_request(
    method: str,
    path: str,
    body: bytes = b"",
    secret: str = CLIENT_SECRET,
    client_id: str = "UnsolvedCaseFiles-v1",
    ts_offset: float = 0.0
) -> Dict[str, str]:
    """Generate valid HMAC security headers for client requests and integration tests."""
    import uuid
    clean_path = path.split("?")[0]
    ts = str(int(time.time() + ts_offset))
    nonce = str(uuid.uuid4())
    body_hash = hashlib.sha256(body if body else b"").hexdigest()
    canonical = f"{method.upper()}\n{clean_path}\n{ts}\n{nonce}\n{body_hash}"
    sig = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return {
        "X-Game-Client": client_id,
        "X-Game-Timestamp": ts,
        "X-Game-Nonce": nonce,
        "X-Game-Signature": sig
    }


class ClientIntegrityMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to enforce client integrity checks."""

    # Whitelisted paths that do not require game client authentication
    WHITELISTED_EXACT = {
        "/",
        "/health",
        "/api/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    }

    async def dispatch(self, request: Request, call_next):
        # Always allow CORS pre-flight OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # Allow public health check, swagger docs, and static asset downloads
        if path in self.WHITELISTED_EXACT or path.startswith("/static/"):
            return await call_next(request)

        # Allow WebSocket upgrades (they do handshake via ASGI)
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Read security headers
        client_id = request.headers.get("X-Game-Client", "")
        timestamp = request.headers.get("X-Game-Timestamp", "")
        nonce = request.headers.get("X-Game-Nonce", "")
        signature = request.headers.get("X-Game-Signature", "")

        # Read body bytes (cached in request for downstream route handlers)
        body = await request.body()

        # Validate
        is_valid, reason = verify_signature(
            method=request.method,
            path=path,
            client_id=client_id,
            timestamp_str=timestamp,
            nonce=nonce,
            signature=signature,
            body_bytes=body
        )

        if not is_valid:
            logger.warning(
                f"[SECURITY] Unauthorized access blocked: {request.method} {path} | "
                f"Client: '{client_id}' | Reason: {reason}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "status_code": 403,
                    "detail": f"Access Denied: {reason}. Only the official Unsolved Case Files game client is authorized.",
                    "security_model": "HMAC-SHA256 Client Integrity Verification"
                }
            )

        # Check Rate Limit for expensive generation endpoint
        if path == "/api/case/generate" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            allowed, retry_after = check_rate_limit(client_ip)
            if not allowed:
                logger.warning(f"[SECURITY] Rate limit exceeded for IP {client_ip} on {path}. Retry after {retry_after}s.")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "status_code": 429,
                        "detail": f"Rate limit exceeded: Tối đa {RATE_LIMIT_CASE_GEN_PER_MIN} yêu cầu sinh vụ án mỗi phút. Vui lòng thử lại sau {retry_after} giây.",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )

        return await call_next(request)
