"""
Tests for configuration management.
"""

import pytest
from unittest.mock import patch
import os

from app.config import Settings, get_settings


def test_default_settings():
    """Test default settings values."""
    settings = Settings()

    assert settings.environment == "development"
    assert settings.debug is True
    assert settings.allowed_origins == ["*"]
    assert (
        settings.database_url
        == "postgresql+asyncpg://postgres:password@localhost:5432/agri_platform"
    )
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.max_response_time_seconds == 3
    assert settings.default_language == "en"
    assert "hi" in settings.supported_languages
    assert settings.log_level == "INFO"


def test_settings_from_env():
    """Test settings loaded from environment variables."""
    with patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "DATABASE_URL": "postgresql://prod:pass@prod-db:5432/prod_db",
            "MAX_RESPONSE_TIME_SECONDS": "5",
            "LOG_LEVEL": "WARNING",
        },
    ):
        settings = Settings()

        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.database_url == "postgresql://prod:pass@prod-db:5432/prod_db"
        assert settings.max_response_time_seconds == 5
        assert settings.log_level == "WARNING"


def test_get_settings_cached():
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    # Should be the same instance due to lru_cache
    assert settings1 is settings2


def test_supported_languages():
    """Test supported languages configuration."""
    settings = Settings()

    expected_languages = ["en", "hi", "bn", "te", "ta", "mr", "gu", "kn", "ml", "or"]
    assert settings.supported_languages == expected_languages

    # Test that English is always included
    assert "en" in settings.supported_languages


def test_security_settings():
    """Test security-related settings."""
    settings = Settings()

    assert settings.secret_key == "your-secret-key-change-in-production"
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
