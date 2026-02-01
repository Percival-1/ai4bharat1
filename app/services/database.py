"""
Database service layer with basic CRUD operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    User,
    Session,
    MarketPrice,
    NotificationPreferences,
    NotificationHistory,
)


class UserService:
    """Service for user-related database operations."""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_phone(db: AsyncSession, phone_number: str) -> Optional[User]:
        """Get user by phone number."""
        result = await db.execute(select(User).where(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession, user_id: UUID, user_data: Dict[str, Any]
    ) -> Optional[User]:
        """Update user information."""
        await db.execute(update(User).where(User.id == user_id).values(**user_data))
        await db.commit()
        return await UserService.get_user_by_id(db, user_id)

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
        """Delete a user."""
        result = await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_users_by_location(
        db: AsyncSession, district: Optional[str] = None, state: Optional[str] = None
    ) -> List[User]:
        """Get users by location."""
        query = select(User)

        if district:
            query = query.where(User.district == district)
        if state:
            query = query.where(User.state == state)

        result = await db.execute(query)
        return list(result.scalars().all())


class SessionService:
    """Service for session-related database operations."""

    @staticmethod
    async def create_session(db: AsyncSession, session_data: Dict[str, Any]) -> Session:
        """Create a new session."""
        session = Session(**session_data)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session_by_id(
        db: AsyncSession, session_id: UUID
    ) -> Optional[Session]:
        """Get session by ID."""
        result = await db.execute(
            select(Session)
            .options(selectinload(Session.user))
            .where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_session_by_user(
        db: AsyncSession, user_id: UUID, channel: Optional[str] = None
    ) -> Optional[Session]:
        """Get active session for a user."""
        query = select(Session).where(
            Session.user_id == user_id, Session.is_active == True
        )

        if channel:
            query = query.where(Session.channel == channel)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session(
        db: AsyncSession, session_id: UUID, session_data: Dict[str, Any]
    ) -> Optional[Session]:
        """Update session information."""
        await db.execute(
            update(Session).where(Session.id == session_id).values(**session_data)
        )
        await db.commit()
        return await SessionService.get_session_by_id(db, session_id)

    @staticmethod
    async def deactivate_session(db: AsyncSession, session_id: UUID) -> bool:
        """Deactivate a session."""
        result = await db.execute(
            update(Session).where(Session.id == session_id).values(is_active=False)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def cleanup_inactive_sessions(db: AsyncSession, hours: int = 24) -> int:
        """Clean up inactive sessions older than specified hours."""
        from datetime import datetime, timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await db.execute(
            delete(Session).where(
                Session.last_activity < cutoff_time, Session.is_active == False
            )
        )
        await db.commit()
        return result.rowcount


class MarketPriceService:
    """Service for market price-related database operations."""

    @staticmethod
    async def create_market_price(
        db: AsyncSession, price_data: Dict[str, Any]
    ) -> MarketPrice:
        """Create a new market price record."""
        market_price = MarketPrice(**price_data)
        db.add(market_price)
        await db.commit()
        await db.refresh(market_price)
        return market_price

    @staticmethod
    async def get_latest_prices_by_crop(
        db: AsyncSession, crop_name: str, limit: int = 10
    ) -> List[MarketPrice]:
        """Get latest prices for a specific crop."""
        result = await db.execute(
            select(MarketPrice)
            .where(MarketPrice.crop_name == crop_name)
            .order_by(MarketPrice.date.desc(), MarketPrice.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_prices_by_location(
        db: AsyncSession,
        district: Optional[str] = None,
        state: Optional[str] = None,
        crop_name: Optional[str] = None,
    ) -> List[MarketPrice]:
        """Get market prices by location."""
        query = select(MarketPrice).order_by(MarketPrice.date.desc())

        if district:
            query = query.where(MarketPrice.district == district)
        if state:
            query = query.where(MarketPrice.state == state)
        if crop_name:
            query = query.where(MarketPrice.crop_name == crop_name)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_price_trends(
        db: AsyncSession, crop_name: str, days: int = 30
    ) -> List[MarketPrice]:
        """Get price trends for a crop over specified days."""
        from datetime import date, timedelta

        start_date = date.today() - timedelta(days=days)

        result = await db.execute(
            select(MarketPrice)
            .where(MarketPrice.crop_name == crop_name, MarketPrice.date >= start_date)
            .order_by(MarketPrice.date.desc())
        )
        return list(result.scalars().all())


class NotificationService:
    """Service for notification-related database operations."""

    @staticmethod
    async def create_notification_preferences(
        db: AsyncSession, prefs_data: Dict[str, Any]
    ) -> NotificationPreferences:
        """Create notification preferences for a user."""
        prefs = NotificationPreferences(**prefs_data)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        return prefs

    @staticmethod
    async def get_notification_preferences(
        db: AsyncSession, user_id: UUID
    ) -> Optional[NotificationPreferences]:
        """Get notification preferences for a user."""
        result = await db.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_notification_preferences(
        db: AsyncSession, user_id: UUID, prefs_data: Dict[str, Any]
    ) -> Optional[NotificationPreferences]:
        """Update notification preferences."""
        await db.execute(
            update(NotificationPreferences)
            .where(NotificationPreferences.user_id == user_id)
            .values(**prefs_data)
        )
        await db.commit()
        return await NotificationService.get_notification_preferences(db, user_id)

    @staticmethod
    async def create_notification_history(
        db: AsyncSession, history_data: Dict[str, Any]
    ) -> NotificationHistory:
        """Create a notification history record."""
        history = NotificationHistory(**history_data)
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history

    @staticmethod
    async def get_notification_history(
        db: AsyncSession, user_id: UUID, limit: int = 50
    ) -> List[NotificationHistory]:
        """Get notification history for a user."""
        result = await db.execute(
            select(NotificationHistory)
            .where(NotificationHistory.user_id == user_id)
            .order_by(NotificationHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_delivery_status(
        db: AsyncSession,
        notification_id: UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update notification delivery status."""
        update_data = {"delivery_status": status}
        if error_message:
            update_data["error_message"] = error_message

        result = await db.execute(
            update(NotificationHistory)
            .where(NotificationHistory.id == notification_id)
            .values(**update_data)
        )
        await db.commit()
        return result.rowcount > 0
