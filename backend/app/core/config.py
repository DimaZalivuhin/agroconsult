"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for the AgroConsult backend.

    All values are loaded from the environment (or .env file in dev).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- Application ----------
    app_name: str = "AgroConsult"
    app_env: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ---------- Security ----------
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    # ---------- Database ----------
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agroconsult"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/agroconsult"

    # ---------- Qdrant ----------
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "agroconsult_docs"
    qdrant_vector_size: int = 1024

    # ---------- Redis ----------
    upstash_redis_url: str | None = None
    upstash_redis_token: str | None = None
    redis_cache_ttl: int = 3600

    # ---------- GigaChat ----------
    gigachat_client_id: str | None = None
    gigachat_client_secret: str | None = None
    gigachat_auth_key: str | None = None
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat-Pro"
    gigachat_embeddings_model: str = "Embeddings"
    gigachat_base_url: str = "https://gigachat.devices.sberbank.ru/api/v1"
    gigachat_auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    # ---------- RAG ----------
    rag_top_k_retrieval: int = 15
    rag_top_k_context: int = 6
    rag_max_context_tokens: int = 4000
    rag_temperature: float = 0.2
    rag_chunk_size: int = 900
    rag_chunk_overlap: int = 150

    # ---------- Admin ----------
    admin_email: str = "admin@agroconsult.local"
    admin_password: str = "change-me"

    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() in ("dev", "development", "local")


@lru_cache
def get_settings() -> Settings:
    """Singleton accessor for settings."""
    return Settings()


settings = get_settings()
