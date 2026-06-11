import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

def _resolve_env_file() -> Path | str:
    root_dir = Path(__file__).parent.parent
    env_file = root_dir / ".env"
    if env_file.exists():
        return env_file
    raise FileNotFoundError(f".env file not found in {root_dir}")

class Settings(BaseSettings):
    qdrant_host: str = "http://localhost:6333"
    collection_name: str = "ask_to_pdf_collection"

    groq_api_key: str = "GROQ_API_KEY"
    openai_api_key: str = "OPENAI_API_KEY"
    model_name: str = "all-MiniLM-L6-v2"
    model_device: str = "cpu"
    groq_model: str = "llama"  # or "ollama"

    class Config:
        env_file = _resolve_env_file()
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()