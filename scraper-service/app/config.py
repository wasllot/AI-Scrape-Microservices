"""
Scraper Service Configuration Module

Centralized configuration management with validation.
Environment-specific config: .env, .env.staging, .env.production
Set ENV=staging or ENV=production to load different configs.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Scraper service settings with validation.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    env: str = Field(default="development", env="ENV")
    
    # Application Configuration
    app_name: str = Field(default="Universal Scraper Service", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    allowed_origins: str = Field(default="http://localhost:3000", env="ALLOWED_ORIGINS")
    
    # Playwright Configuration
    headless: bool = Field(default=True, env="PLAYWRIGHT_HEADLESS")
    timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="USER_AGENT"
    )
    browser_contexts: int = Field(default=5, env="PLAYWRIGHT_CONTEXTS")
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    requests_per_minute: int = Field(default=60, env="REQUESTS_PER_MINUTE")
    
    # Redis Configuration (for caching)
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=1, env="REDIS_DB")
    
    @field_validator("timeout", "requests_per_minute", mode="before")
    @classmethod
    def validate_positive_int(cls, v):
        """Validate positive integer values"""
        if isinstance(v, str):
            v = int(v)
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
    
    @model_validator(mode="after")
    def validate_environment(self):
        """Validate environment-specific settings"""
        if self.env == "production":
            if self.debug:
                raise ValueError("DEBUG must be False in production")
            if self.allowed_origins == "*":
                raise ValueError("CORS cannot be open (*) in production")
            if not self.cache_enabled:
                raise ValueError("Cache must be enabled in production")
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
    def allowed_origins_list(self) -> list:
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
    """
    env = os.getenv("ENV", "development")
    return Settings(_env_file=f".env.{env}" if env != "development" else ".env")


settings = get_settings()
