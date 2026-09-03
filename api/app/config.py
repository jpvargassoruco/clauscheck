from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    ENV: str = "dev"
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@postgres:5432/clauscheck"
    )
    POSTGRES_PASSWORD: str = "postgres"
    REDIS_URL: str = "redis://redis:6379/0"

    # Paperless
    PAPERLESS_URL: str = "http://paperless:8000"
    PAPERLESS_API_TOKEN: str = ""

    # Auth
    JWT_SECRET: str = "dev-secret-change-me-please-32-bytes-min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Fernet key for encrypting llm_providers.api_key_enc
    FERNET_KEY: str = ""

    # LLM env fallbacks
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    MOONSHOT_API_KEY: str = ""
    MOONSHOT_BASE_URL: str = "https://api.moonshot.ai/v1"
    MOONSHOT_MODEL: str = "moonshot-v1-8k"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openrouter/auto"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"

    # Embeddings
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    EMBEDDING_DIM: int = 384

    # Pipeline: pseudonymize PII before every LLM call, restore on persistence.
    PSEUDONYMIZE: bool = True

    # Seed / bootstrap
    ADMIN_EMAIL: str = "admin@clauscheck.local"
    ADMIN_PASSWORD: str = "changeme"

    # Registro / solicitudes de acceso
    REGISTRATION_MODE: str = "approval"  # open|approval|closed

    # Correo saliente
    MAIL_BACKEND: str = "console"  # console|smtp
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    SMTP_FROM_NAME: str = "ClausCheck"
    ADMIN_NOTIFY_EMAIL: str = ""

    # Base URL pública de la web (para enlaces en correos)
    APP_BASE_URL: str = "http://localhost:8080"

    # Límites de tamaño de documento (abuso), independientes del plan.
    MAX_TEXTO_CHARS: int = 200_000
    MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024
    MAX_PALABRAS_DOC: int = 40_000

    # Tasa de cambio USD -> Bs usada solo para el dashboard de consumo.
    USD_BOB: float = 6.96

    @property
    def database_url_resolved(self) -> str:
        return self.DATABASE_URL.replace("${POSTGRES_PASSWORD}", self.POSTGRES_PASSWORD)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
