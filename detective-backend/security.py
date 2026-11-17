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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("security")

DEFAULT_SECRET = "Phenikaa_UCF_AI_SecretKey_2026_SecureHmacKey_x9!"
CLIENT_SECRET = os.getenv("GAME_CLIENT_SECRET", DEFAULT_SECRET)
REQUIRE_SIGNATURE = os.getenv("REQUIRE_CLIENT_SIGNATURE", "true").lower() in ("true", "1", "yes")

# Max allowed time drift between client and server (in seconds)
MAX_TIME_DRIFT = 60.0

# In-memory sliding window nonce cache: nonce -> timestamp
_SEEN_NONCES: Dict[str, float] = {}


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

        return await call_next(request)
