#!/usr/bin/env python3
"""
Database seeding script for the agri-civic intelligence platform.
"""

import asyncio
import sys
from datetime import date, time
from pathlib import Path
from uuid import uuid4

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, engine
from app.models import User, MarketPrice, NotificationPreferences


async def seed_sample_data():
    """Seed the database with sample data for development and testing."""

    print("🌱 Seeding database with sample data...")

    async with AsyncSessionLocal() as session:
        try:
            # Create sample users
            users_data = [
                {
                    "phone_number": "+919876543210",
                    "preferred_language": "hi",
                    "location_lat": 28.6139,
                    "location_lng": 77.2090,
                    "location_address": "New Delhi, India",
                    "district": "New Delhi",
                    "state": "Delhi",
                    "crops": ["wheat", "rice"],
                    "name": "राम कुमार",
                },
                {
                    "phone_number": "+919876543211",
                    "preferred_language": "te",
                    "location_lat": 17.3850,
                    "location_lng": 78.4867,
                    "location_address": "Hyderabad, Telangana, India",
                    "district": "Hyderabad",
                    "state": "Telangana",
                    "crops": ["cotton", "maize"],
                    "name": "వెంకట రావు",
                },
                {
                    "phone_number": "+919876543212",
                    "preferred_language": "ta",
                    "location_lat": 13.0827,
                    "location_lng": 80.2707,
                    "location_address": "Chennai, Tamil Nadu, India",
                    "district": "Chennai",
                    "state": "Tamil Nadu",
                    "crops": ["rice", "sugarcane"],
                    "name": "முருகன்",
                },
            ]

            created_users = []
            for user_data in users_data:
                user = User(**user_data)
                session.add(user)
                created_users.append(user)

            await session.flush()  # Flush to get user IDs

            # Create notification preferences for users
            for user in created_users:
                notification_prefs = NotificationPreferences(
                    user_id=user.id,
                    daily_msp_updates=True,
                    weather_alerts=True,
                    scheme_notifications=True,
                    market_price_alerts=True,
                    preferred_channels=["sms", "voice"],
                    preferred_time=time(8, 0),
                    notification_frequency="daily",
                    notification_language=user.preferred_language,
                )
                session.add(notification_prefs)

            # Create sample market price data
            market_data = [
                {
                    "mandi_name": "Azadpur Mandi",
                    "crop_name": "wheat",
                    "price_per_quintal": 2150.00,
                    "date": date.today(),
                    "location_lat": 28.7041,
                    "location_lng": 77.1025,
                    "location_address": "Azadpur, Delhi",
                    "district": "North Delhi",
                    "state": "Delhi",
                    "quality_grade": "FAQ",
                    "source": "AGMARKNET",
                    "previous_price": 2100.00,
                    "price_change_percentage": 2.38,
                },
                {
                    "mandi_name": "Kurnool Market",
                    "crop_name": "cotton",
                    "price_per_quintal": 5800.00,
                    "date": date.today(),
                    "location_lat": 15.8281,
                    "location_lng": 78.0373,
                    "location_address": "Kurnool, Andhra Pradesh",
                    "district": "Kurnool",
                    "state": "Andhra Pradesh",
                    "quality_grade": "Medium",
                    "source": "AGMARKNET",
                    "previous_price": 5750.00,
                    "price_change_percentage": 0.87,
                },
                {
                    "mandi_name": "Thanjavur Market",
                    "crop_name": "rice",
                    "price_per_quintal": 1950.00,
                    "date": date.today(),
                    "location_lat": 10.7870,
                    "location_lng": 79.1378,
                    "location_address": "Thanjavur, Tamil Nadu",
                    "district": "Thanjavur",
                    "state": "Tamil Nadu",
                    "quality_grade": "Common",
                    "source": "AGMARKNET",
                    "previous_price": 1920.00,
                    "price_change_percentage": 1.56,
                },
                {
                    "mandi_name": "Warangal Market",
                    "crop_name": "maize",
                    "price_per_quintal": 1850.00,
                    "date": date.today(),
                    "location_lat": 17.9689,
                    "location_lng": 79.5941,
                    "location_address": "Warangal, Telangana",
                    "district": "Warangal",
                    "state": "Telangana",
                    "quality_grade": "FAQ",
                    "source": "AGMARKNET",
                    "previous_price": 1820.00,
                    "price_change_percentage": 1.65,
                },
            ]

            for market_item in market_data:
                market_price = MarketPrice(**market_item)
                session.add(market_price)

            # Commit all changes
            await session.commit()

            print(f"✅ Successfully seeded database with:")
            print(f"   - {len(users_data)} sample users")
            print(f"   - {len(users_data)} notification preferences")
            print(f"   - {len(market_data)} market price records")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding database: {e}")
            raise

        finally:
            await session.close()


async def clear_sample_data():
    """Clear all sample data from the database."""

    print("🧹 Clearing sample data from database...")

    async with AsyncSessionLocal() as session:
        try:
            # Delete all records (in reverse order due to foreign key constraints)
            await session.execute("DELETE FROM notification_history")
            await session.execute("DELETE FROM notification_preferences")
            await session.execute("DELETE FROM market_prices")
            await session.execute("DELETE FROM sessions")
            await session.execute("DELETE FROM users")

            await session.commit()
            print("✅ Sample data cleared successfully!")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error clearing sample data: {e}")
            raise

        finally:
            await session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database seeding script")
    parser.add_argument(
        "--clear", action="store_true", help="Clear all sample data from the database"
    )

    args = parser.parse_args()

    async def main():
        try:
            if args.clear:
                await clear_sample_data()
            else:
                await seed_sample_data()
        finally:
            await engine.dispose()

    asyncio.run(main())
