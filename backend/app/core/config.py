import secrets
import warnings
from typing import Annotated, Any, Literal, List, Optional, Union, Dict

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
    AnyHttpUrl,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5174"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5174"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    
    # Database Configuration - Support SQLite for development
    USE_SQLITE: bool = True  # Enable SQLite for development
    SQLITE_DB_PATH: str = "rag_system.db"
    
    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite:///./{self.SQLITE_DB_PATH}"
        else:
            return str(MultiHostUrl.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            ))

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def parsed_gemini_api_keys(self) -> list[str]:
        """Parse comma-separated API keys for rotation"""
        if not self.GEMINI_API_KEYS:
            return [self.GEMINI_API_KEY] if self.GEMINI_API_KEY else []
        
        # Split by comma and clean up whitespace
        keys = [key.strip() for key in self.GEMINI_API_KEYS.split(",") if key.strip()]
        
        # Add primary key if not already included
        if self.GEMINI_API_KEY and self.GEMINI_API_KEY not in keys:
            keys.insert(0, self.GEMINI_API_KEY)
        
        return keys

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # RAG System Configuration
    # AI Models and APIs (Updated to Gemini 2.5 Flash-Lite Preview)
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash-lite-preview-06-17"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_EMBEDDING_DIMENSION: int = 3072  # Elastic: 3072, 1536, or 768
    OPENAI_API_KEY: str = ""  # For embeddings (text-embedding-3-small)
    
    # Multiple API Keys for Rotation (comma-separated)
    GEMINI_API_KEYS: str = ""  # Format: "key1,key2,key3,..." for rotation
    USE_API_ROTATION: bool = False  # Enable multi-key rotation
    
    @model_validator(mode='after')  # Context7: Auto-enable rotation when multiple keys available
    def validate_api_rotation(self) -> Self:
        """Auto-enable API rotation when multiple Gemini API keys are provided"""
        parsed_keys = self.parsed_gemini_api_keys
        if len(parsed_keys) > 1:
            print(f"🔄 Auto-enabling API rotation: {len(parsed_keys)} keys detected")
            self.USE_API_ROTATION = True
        else:
            print(f"🔑 Single API key mode: {len(parsed_keys)} key(s)")
        return self
    
    # Text Processing Settings (from PRD requirements)
    CHUNK_SIZE: int = 1000  # Character-based chunking
    CHUNK_OVERLAP: int = 200  # Overlap between chunks
    MIN_CHUNK_SIZE: int = 50  # Minimum chunk size to keep
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB from PRD
    
    # File Storage
    UPLOAD_DIR: str = "uploads"  # Directory for uploaded files
    
    # Vector Database (Pinecone)
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "rag-index"
    
    # Redis Configuration (for caching)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Rate Limiting (based on Gemini free tier)
    MAX_REQUESTS_PER_MINUTE: int = 15  # Gemini Flash-Lite Preview limit
    MAX_REQUESTS_PER_DAY: int = 1000   # Daily limit from PRD
    
    # Query Settings
    DEFAULT_TOP_K: int = 10  # Number of chunks to retrieve (optimized)
    DEFAULT_TEMPERATURE: float = 0.3  # LLM temperature
    MAX_QUERY_LENGTH: int = 500  # Maximum query characters
    SIMILARITY_THRESHOLD: float = 0.25  # Minimum similarity for retrieval (optimized for Sentence Transformers)

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        
        # Only check PostgreSQL password if not using SQLite
        if not self.USE_SQLITE:
            self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
            
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
