import uuid
import time
import sys
from loguru import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# ── Loguru config ──────────────────────────────────────────────
logger.remove()  # Remove default handler
logger.configure(extra={"request_id": "system"})

# Console: coloured, human-readable
logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[request_id]}</cyan> | "
        "<white>{name}:{function}:{line}</white> | "
        "{message}"
    ),
    level="INFO",
)

# File: JSON-friendly, rotates daily, kept 7 days
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    compression="zip",
    format="{time} | {level} | {extra[request_id]} | {name}:{line} | {message}",
    level="DEBUG",
    serialize=True,   # writes as JSON — easy to ship to ELK/Datadog
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Attaches a short request_id to every request.
    Logs method, path, status, and duration automatically.
    Injects X-Request-ID into response headers.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]          # e.g. "a3f1bc92"
        request.state.request_id = request_id        # available in route handlers

        start = time.perf_counter()
        response = None

        with logger.contextualize(request_id=request_id):
            logger.info(f"-> {request.method} {request.url.path}")
            try:
                response = await call_next(request)
            except Exception as exc:
                logger.exception(f"Unhandled error: {exc}")
                raise
            finally:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                status_code = response.status_code if response is not None else 500
                logger.info(f"<- {status_code} | {duration_ms}ms")

        response.headers["X-Request-ID"] = request_id
        return response