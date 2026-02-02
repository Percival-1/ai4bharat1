"""
Configuration management for the AI-Driven Agri-Civic Intelligence Platform.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application settings
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(default=True, description="Debug mode")
    allowed_origins: List[str] = Field(
        default=["*"], description="CORS allowed origins"
    )

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/agri_platform",
        description="Database URL",
    )

    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")

    # External API settings
    openai_api_key: str = Field(default="", description="OpenAI API key")
    google_translate_api_key: str = Field(
        default="", description="Google Translate API key"
    )

    google_maps_api_key: str = Field(default="", description="Google Maps API key")
    openweather_api_key: str = Field(default="", description="OpenWeatherMap API key")

    # Vector Database settings
    vector_db_type: str = Field(
        default="chromadb",
        description="Vector database type (chromadb, pinecone, weaviate)",
    )

    # ChromaDB settings
    chroma_host: str = Field(default="localhost", description="ChromaDB host")
    chroma_port: int = Field(default=8000, description="ChromaDB port")
    chroma_persist_directory: str = Field(
        default="./data/chroma_db", description="ChromaDB persistence directory"
    )

    # Pinecone settings (alternative)
    pinecone_api_key: str = Field(default="", description="Pinecone API key")
    pinecone_environment: str = Field(default="", description="Pinecone environment")
    pinecone_index_name: str = Field(
        default="agri-platform", description="Pinecone index name"
    )

    # Weaviate settings (alternative)
    weaviate_url: str = Field(
        default="http://localhost:8080", description="Weaviate URL"
    )
    weaviate_api_key: str = Field(default="", description="Weaviate API key")

    twilio_account_sid: str = Field(default="", description="Twilio Account SID")
    twilio_auth_token: str = Field(default="", description="Twilio Auth Token")
    twilio_phone_number: str = Field(default="", description="Twilio Phone Number")

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production", description="Secret key for JWT"
    )

    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )

    # Application settings
    max_response_time_seconds: int = Field(
        default=3, description="Maximum response time in seconds"
    )

    default_language: str = Field(default="en", description="Default language")
    supported_languages: List[str] = Field(
        default=["en", "hi", "bn", "te", "ta", "mr", "gu", "kn", "ml", "or"],
        description="Supported languages",
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
