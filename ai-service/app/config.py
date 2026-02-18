"""
AI Service Configuration Module

This module provides configuration management following the Single Responsibility Principle.
All configuration is centralized and validated here.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Uses Pydantic for automatic validation and type checking.
    Environment variables are automatically loaded.
    """
    
    # Database Configuration
    postgres_host: str = Field(default="postgres", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="vector_db", env="POSTGRES_DB")
    
    # AI Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    embedding_model: str = Field(default="models/embedding-001", env="EMBEDDING_MODEL")
    chat_model: str = Field(default="models/gemini-1.5-flash", env="CHAT_MODEL")
    embedding_dimension: int = Field(default=768, env="EMBEDDING_DIMENSION")
    
    # Redis Configuration
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Application Configuration
    app_name: str = Field(default="AI & RAG Engine", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    
    @validator("gemini_api_key")
    def validate_api_key(cls, v):
        """Ensure API key is not empty"""
        if not v or v == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY must be set to a valid API key")
        return v
    
    @property
    def database_url(self) -> str:
        """Construct database connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()
