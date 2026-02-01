#!/usr/bin/env python3
"""
Database initialization script for the agri-civic intelligence platform.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import create_tables, drop_tables, engine
from app.config import get_settings


async def init_database():
    """Initialize the database by creating all tables."""
    settings = get_settings()

    print(f"Initializing database at: {settings.database_url}")

    try:
        # Create all tables
        await create_tables()
        print("✅ Database tables created successfully!")

    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise

    finally:
        # Close database connections
        await engine.dispose()


async def reset_database():
    """Reset the database by dropping and recreating all tables."""
    settings = get_settings()

    print(f"Resetting database at: {settings.database_url}")

    try:
        # Drop all tables
        await drop_tables()
        print("🗑️  Database tables dropped successfully!")

        # Create all tables
        await create_tables()
        print("✅ Database tables created successfully!")

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        raise

    finally:
        # Close database connections
        await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database by dropping and recreating all tables",
    )

    args = parser.parse_args()

    if args.reset:
        asyncio.run(reset_database())
    else:
        asyncio.run(init_database())
