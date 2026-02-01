"""
Notification models for managing user preferences and notification history.
"""

from datetime import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import ARRAY, Boolean, ForeignKey, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class NotificationPreferences(Base):
    """Notification preferences model for managing user notification settings."""

    __tablename__ = "notification_preferences"

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Notification type preferences
    daily_msp_updates: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    weather_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scheme_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    market_price_alerts: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Channel preferences
    preferred_channels: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=["sms"]
    )  # ['sms', 'voice', 'chat', 'ivr']

    # Timing preferences
    preferred_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True, default=time(8, 0)  # 8:00 AM
    )

    # Frequency preferences
    notification_frequency: Mapped[str] = mapped_column(
        String(20), default="daily", nullable=False
    )  # 'daily', 'weekly', 'immediate'

    # Language preference for notifications
    notification_language: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )

    # Additional preferences
    custom_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default={}
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="notification_preferences"
    )

    def __repr__(self) -> str:
        """String representation of notification preferences."""
        return f"<NotificationPreferences(id={self.id}, user_id={self.user_id}, channels={self.preferred_channels})>"


class NotificationHistory(Base):
    """Notification history model for tracking sent notifications."""

    __tablename__ = "notification_history"

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification details
    notification_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'msp_update', 'weather_alert', 'scheme_notification', 'market_alert'

    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 'sms', 'voice', 'chat', 'ivr'

    # Message content
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Delivery information
    delivery_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # 'pending', 'sent', 'delivered', 'failed'

    # Error information (if any)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # External service information
    external_message_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # ID from SMS/voice service provider

    # Additional metadata
    additional_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default={}
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_history")

    def __repr__(self) -> str:
        """String representation of notification history."""
        return f"<NotificationHistory(id={self.id}, user_id={self.user_id}, type={self.notification_type}, status={self.delivery_status})>"
