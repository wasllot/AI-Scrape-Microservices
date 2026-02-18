"""
AI Service Configuration Module

This module provides configuration management following the Single Responsibility Principle.
All configuration is centralized and validated here.

Environment-specific config:
- .env (default, local development)
- .env.staging (staging environment)
- .env.production (production environment)

Set ENV=staging or ENV=production to load different configs.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import Optional, List
import os


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Uses Pydantic for automatic validation and type checking.
    Environment variables are automatically loaded.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    env: str = Field(default="development", env="ENV")
    
    # Database Configuration
    postgres_host: str = Field(default="postgres", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="vector_db", env="POSTGRES_DB")
    postgres_pool_size: int = Field(default=10, env="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=20, env="POSTGRES_MAX_OVERFLOW")
    
    # AI Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    embedding_model: str = Field(default="models/gemini-embedding-001", env="EMBEDDING_MODEL")
    chat_model: str = Field(default="models/gemini-1.5-flash", env="CHAT_MODEL")
    embedding_dimension: int = Field(default=3072, env="EMBEDDING_DIMENSION")
    
    # Redis Configuration
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Application Configuration
    app_name: str = Field(default="AI & RAG Engine", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    allowed_origins: str = Field(default="http://localhost:3000", env="ALLOWED_ORIGINS")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=60, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Data Retention
    retention_messages_days: int = Field(default=90, env="RETENTION_MESSAGES_DAYS")
    retention_conversations_days: int = Field(default=365, env="RETENTION_CONVERSATIONS_DAYS")
    retention_embeddings_days: int = Field(default=365, env="RETENTION_EMBEDDINGS_DAYS")
    data_validation_enabled: bool = Field(default=True, env="DATA_VALIDATION_ENABLED")
    pii_sanitization_enabled: bool = Field(default=True, env="PII_SANITIZATION_ENABLED")
    
    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v):
        """Ensure API key is not empty"""
        if not v or v == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY must be set to a valid API key")
        return v
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def validate_origins(cls, v):
        """Validate and parse allowed origins"""
        if isinstance(v, str):
            return v
        return v
    
    @field_validator("postgres_port", "redis_port", mode="before")
    @classmethod
    def validate_ports(cls, v):
        """Validate port numbers"""
        if isinstance(v, str):
            v = int(v)
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @model_validator(mode="after")
    def validate_environment(self):
        """Validate environment-specific settings"""
        if self.env == "production":
            if self.debug:
                raise ValueError("DEBUG must be False in production")
            if self.postgres_password == "postgres":
                raise ValueError("Default postgres password not allowed in production")
            if self.allowed_origins == "*":
                raise ValueError("CORS cannot be open (*) in production")
        return self
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.env == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.env == "development"
    
    @property
    def database_url(self) -> str:
        """Construct database connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed origins as list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


def get_settings() -> Settings:
    """
    Get settings instance with environment-specific config loading.
    
    Loads .env.{ENV} in addition to .env for environment-specific overrides.
    """
    env = os.getenv("ENV", "development")
    
    settings = Settings(_env_file=f".env.{env}" if env != "development" else ".env")
    return settings


# Default settings instance
settings = get_settings()
