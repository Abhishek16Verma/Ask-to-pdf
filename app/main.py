from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from slowapi.errors import RateLimitExceeded
import uvicorn

from app.api.router import router as api_router
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.observability.langsmith_setup import setup_langsmith
from app.pdf_loader.query import query_object
from app.utils.config import get_settings, get_upload_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.bind(request_id="startup").info("Starting Ask-to-PDF API...")
    setup_langsmith()

    app.state.upload_dir = get_upload_dir()
    app.state.chain = query_object.build_chain()

    logger.bind(request_id="startup").info("RAG chain initialized and ready.")
    yield
    logger.bind(request_id="shutdown").info("Shutting down Ask-to-PDF API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ask to PDF",
        description="RAG pipeline with FastAPI, LangChain, and Qdrant.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )