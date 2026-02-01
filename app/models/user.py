"""
User model for the agri-civic intelligence platform.
"""

from typing import List, Optional

from sqlalchemy import ARRAY, DECIMAL, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    """User model representing farmers and rural community members."""

    __tablename__ = "users"

    # Contact information
    phone_number: Mapped[str] = mapped_column(
        String(15), unique=True, nullable=False, index=True
    )

    # Language preferences
    preferred_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en"
    )

    # Location information
    location_lat: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 8), nullable=True)
    location_lng: Mapped[Optional[float]] = mapped_column(DECIMAL(11, 8), nullable=True)
    location_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Agricultural information
    crops: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=[]
    )

    # User profile information
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    notification_preferences: Mapped[Optional["NotificationPreferences"]] = (
        relationship("NotificationPreferences", back_populates="user", uselist=False)
    )
    notification_history: Mapped[List["NotificationHistory"]] = relationship(
        "NotificationHistory", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, phone={self.phone_number}, lang={self.preferred_language})>"
