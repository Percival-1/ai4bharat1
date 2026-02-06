"""
Test configuration and fixtures.
"""

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects import sqlite
from sqlalchemy import String

from app.models.base import Base
from app.config import get_settings

# Test database URL - using SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Handle UUID type for SQLite
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TypeDecorator, String as SQLString


class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type for SQLite."""

    impl = SQLString
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(SQLString(36))
        else:
            return dialect.type_descriptor(UUID())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "sqlite":
            return str(value)
        else:
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "sqlite":
            import uuid

            return uuid.UUID(value)
        else:
            return value


# Register the UUID type for SQLite
sqlite.base.ischema_names["UUID"] = SQLiteUUID


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a test database session."""
    # Create test engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    # Clean up
    await engine.dispose()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "phone_number": "+1234567890",
        "preferred_language": "en",
        "location_lat": 28.6139,
        "location_lng": 77.2090,
        "district": "New Delhi",
        "state": "Delhi",
        "crops": ["wheat", "rice"],
        "name": "Test Farmer",
    }


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "channel": "sms",
        "context": {"last_query": "weather"},
        "conversation_history": [
            {"message": "Hello", "timestamp": "2024-01-01T10:00:00"}
        ],
        "session_token": "test_token_123",
        "user_preferences": {"language": "hi"},
    }


@pytest.fixture
def sample_market_price_data():
    """Sample market price data for testing."""
    from datetime import date

    return {
        "mandi_name": "Delhi Mandi",
        "crop_name": "wheat",
        "price_per_quintal": 2500.00,
        "date": date.today(),
        "location_lat": 28.6139,
        "location_lng": 77.2090,
        "district": "New Delhi",
        "state": "Delhi",
        "quality_grade": "A",
        "source": "government_portal",
    }
