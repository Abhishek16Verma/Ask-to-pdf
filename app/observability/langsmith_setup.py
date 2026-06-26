"""
LangSmith tracing setup.

How it works:
  - Setting env vars is enough — LangChain auto-instruments all chains/LLMs.
  - We add run_name to every chain call so traces are readable.
  - Startup logs confirm whether tracing is active.

Dashboard: https://smith.langchain.com/
"""
import os

from loguru import logger

from app.utils.config import get_settings


def setup_langsmith() -> bool:
    settings = get_settings()
    if not settings.langchain_api_key:
        logger.bind(request_id="startup").warning(
            "LANGCHAIN_API_KEY not set. LangSmith tracing is disabled."
        )
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint

    logger.bind(request_id="startup").info(
        f"LangSmith tracing enabled for project: {settings.langchain_project}"
    )
    return True