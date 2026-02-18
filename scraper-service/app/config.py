"""
Scraper Service Configuration Module

Centralized configuration management with validation.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Scraper service settings with validation.
    """
    
    # Application Configuration
    app_name: str = Field(default="Universal Scraper Service", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    allowed_origins: str = Field(default="http://localhost:3000", env="ALLOWED_ORIGINS")
    
    # Playwright Configuration
    headless: bool = Field(default=True, env="PLAYWRIGHT_HEADLESS")
    timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")  # milliseconds
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="USER_AGENT"
    )
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # seconds
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    requests_per_minute: int = Field(default=60, env="REQUESTS_PER_MINUTE")
    
    # Redis Configuration (for caching)
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()
