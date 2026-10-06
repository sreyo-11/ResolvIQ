from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    embedding_cache_dir: str = str(BACKEND_DIR / ".model_cache")
    db_pool_min: int = 1
    db_pool_max: int = 5

    # --- LLM providers ---
    llm_provider: str = "groq"  # groq | gemini
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"

    # --- AI behaviour ---
    category_threshold: float = 0.6   # below this -> LLM fallback / human triage
    priority_threshold: float = 0.5
    kb_min_similarity: float = 0.35   # below this -> refuse to draft (tune with ml.eval_rag)
    rag_top_k: int = 4
    auto_enrich: bool = True          # run the background pipeline on new tickets
    auto_draft: bool = True
    trend_z_threshold: float = 3.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()