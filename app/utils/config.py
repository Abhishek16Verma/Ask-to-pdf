from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_env_file() -> Path:
    env_file = get_project_root() / ".env"
    return env_file


class Settings(BaseSettings):
    app_host: str = "0.0.0.0"
    app_port: int = 8585
    app_reload: bool = True

    qdrant_host: str = "http://localhost:6333"
    qdrant_url: str = "http://localhost:6333"
    redis_host: str = "redis://localhost:6379"
    collection_name: str = "ask_to_pdf_collection"

    groq_api_key: str = ""
    openai_api_key: str = ""
    model_name: str = "all-MiniLM-L6-v2"
    model_device: str = "cpu"
    groq_model: str = "llama-3.1-8b-instant"

    langchain_api_key: str = ""
    langchain_project: str = "ask-to-pdf-rag"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    rate_limit_default: str = "100/hour"
    rate_limit_ask: str = "10/minute"
    rate_limit_upload: str = "5/minute"

    upload_dir: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_upload_dir() -> Path:
    upload_path = Path(get_settings().upload_dir)
    if not upload_path.is_absolute():
        upload_path = get_project_root() / upload_path
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path