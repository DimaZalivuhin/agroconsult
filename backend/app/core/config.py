"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field
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
        populate_by_name=True,
    )

    # ---------- Application ----------
    app_name: str = "AgroConsult"
    app_env: str = "production"
    debug: bool = False
    log_level: str = "INFO"

    # Stored as raw comma-separated string so pydantic-settings doesn't try
    # to JSON-decode it. Access the parsed list via the `cors_origins` property.
    # Validation alias maps the env var CORS_ORIGINS to this field.
    cors_origins_raw: str = Field(default="http://localhost:3000", validation_alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

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
    # GigaChat uses Russian Trusted Root CA (Минцифры), not in default trust store
    # on most Linux images. Set to False to skip SSL verification (acceptable for
    # MVP, as we only talk to Sber domains). For production, install the cert
    # and keep True.
    gigachat_verify_ssl: bool = True

    # ---------- RAG ----------
    rag_top_k_retrieval: int = 15
    rag_top_k_context: int = 6
    rag_max_context_tokens: int = 4000
    rag_temperature: float = 0.2
    # rag_chunk_size of 900 was too aggressive: GigaChat /embeddings rejects
    # inputs larger than ~514 tokens with 413 Payload Too Large. We target
    # 450 tokens per chunk with 90 overlap — fits comfortably under the limit
    # and gives more focused retrieval as a bonus.
    rag_chunk_size: int = 450
    rag_chunk_overlap: int = 90

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
