"""
Session model for managing user conversations and context.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Session(Base):
    """Session model for managing user conversation context across channels."""

    __tablename__ = "sessions"

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Channel information
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 'voice', 'sms', 'chat', 'ivr'

    # Session context and state
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default={}
    )

    # Conversation history
    conversation_history: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=[]
    )

    # Session metadata
    session_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Activity tracking
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    # Session status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Additional session data
    user_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default={}
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        """String representation of the session."""
        return f"<Session(id={self.id}, user_id={self.user_id}, channel={self.channel}, active={self.is_active})>"
