"""Central slowapi configuration for app-wide rate limiting."""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.utils.config import get_settings

settings = get_settings()


def get_rate_limit_key(request: Request) -> str:
    """Prefer user identity when available, otherwise fallback to client IP."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[settings.rate_limit_default],
)

ASK_LIMIT = settings.rate_limit_ask
UPLOAD_LIMIT = settings.rate_limit_upload


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a clean, request-id aware 429 response."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": str(exc.detail),
            "retry_after": "60 seconds",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
        headers={"Retry-After": "60"},
    )