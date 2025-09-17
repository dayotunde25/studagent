"""
Application configuration settings.
"""
import secrets
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project
    PROJECT_NAME: str = "Studagent"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DEBUG: bool = True

    # Server
    SERVER_NAME: str = "Studagent API"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./studagent.db"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # FastAPI
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[str, List[str]]
    ) -> Union[List[str], str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # API Keys
    OPENROUTER_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    # LLM Configuration
    DEFAULT_MODEL_PRIORITY: List[str] = [
        "mistral-7b",
        "mixtral-8x7b",
        "llama-3-8b",
        "mistral-instruct",
        "gemma-7b",
        "groq",
        "gemini"
    ]
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_WINDOW_MINUTES: int = 10
    CIRCUIT_BREAKER_SKIP_MINUTES: int = 30
    LLM_TIMEOUT_SECONDS: int = 15
    LLM_MAX_RETRIES: int = 3
    LLM_BACKOFF_FACTOR: int = 2

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 8001

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_MINUTES: int = 15

    # GDPR
    DATA_RETENTION_DAYS: int = 365

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()