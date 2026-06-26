"""
Helper: get a logger bound with the current request_id.
Use inside route handlers instead of plain logger.

Usage:
    from app.utils.log import get_logger

    @app.post("/ask")
    async def ask(request: Request, ...):
        log = get_logger(request)
        log.info("Processing query", query=query.text)
"""
from loguru import logger
from fastapi import Request


def get_logger(request: Request):
    request_id = getattr(request.state, "request_id", "no-id")
    return logger.bind(request_id=request_id)