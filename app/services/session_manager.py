"""
Session Manager Service for managing user conversation context across channels.

This service handles session lifecycle management, context persistence,
cross-channel continuity, and session cleanup mechanisms.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Session, User
from app.services.database import SessionService, UserService

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session Manager for handling user conversation context and state management.

    Provides session lifecycle management, context persistence, cross-channel
    continuity, and automatic cleanup mechanisms.
    """

    def __init__(self, session_timeout_hours: int = 24):
        """
        Initialize the Session Manager.

        Args:
            session_timeout_hours: Hours after which inactive sessions expire
        """
        self.session_timeout_hours = session_timeout_hours
        self.logger = logger

    async def create_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        channel: str,
        initial_context: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        Create a new session for a user.

        Args:
            db: Database session
            user_id: User ID
            channel: Communication channel ('voice', 'sms', 'chat', 'ivr')
            initial_context: Initial context data
            user_preferences: User preferences for the session

        Returns:
            Created session object
        """
        try:
            # Generate session token
            session_token = str(uuid4())

            # Prepare session data
            session_data = {
                "user_id": user_id,
                "channel": channel,
                "context": initial_context or {},
                "conversation_history": [],
                "session_token": session_token,
                "user_preferences": user_preferences or {},
                "is_active": True,
            }

            # Create session in database
            session = await SessionService.create_session(db, session_data)

            self.logger.info(
                f"Created new session {session.id} for user {user_id} on channel {channel}"
            )

            return session

        except Exception as e:
            self.logger.error(f"Failed to create session for user {user_id}: {str(e)}")
            raise

    async def get_or_create_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        channel: str,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        Get existing active session or create a new one.

        Args:
            db: Database session
            user_id: User ID
            channel: Communication channel
            initial_context: Initial context if creating new session

        Returns:
            Session object (existing or newly created)
        """
        try:
            # Try to get existing active session for the channel
            existing_session = await SessionService.get_active_session_by_user(
                db, user_id, channel
            )

            if existing_session:
                # Update last activity
                await self.update_session_activity(db, existing_session.id)
                self.logger.info(
                    f"Retrieved existing session {existing_session.id} for user {user_id}"
                )
                return existing_session

            # Create new session if none exists
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Use user data as initial context
            user_context = {
                "location": {
                    "lat": float(user.location_lat) if user.location_lat else None,
                    "lng": float(user.location_lng) if user.location_lng else None,
                    "address": user.location_address,
                    "district": user.district,
                    "state": user.state,
                },
                "crops": user.crops or [],
                "preferred_language": user.preferred_language,
                "name": user.name,
            }

            # Merge with provided initial context
            if initial_context:
                user_context.update(initial_context)

            session = await self.create_session(db, user_id, channel, user_context)

            return session

        except Exception as e:
            self.logger.error(
                f"Failed to get or create session for user {user_id}: {str(e)}"
            )
            raise

    async def get_session(
        self, db: AsyncSession, session_id: UUID
    ) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            Session object if found, None otherwise
        """
        try:
            session = await SessionService.get_session_by_id(db, session_id)

            if session and session.is_active:
                # Check if session has expired
                if self._is_session_expired(session):
                    await self.deactivate_session(db, session_id)
                    return None

                # Update last activity
                await self.update_session_activity(db, session_id)

            return session

        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {str(e)}")
            raise

    async def update_session_context(
        self,
        db: AsyncSession,
        session_id: UUID,
        context_updates: Dict[str, Any],
        merge: bool = True,
    ) -> Optional[Session]:
        """
        Update session context.

        Args:
            db: Database session
            session_id: Session ID
            context_updates: Context data to update
            merge: Whether to merge with existing context or replace

        Returns:
            Updated session object
        """
        try:
            session = await SessionService.get_session_by_id(db, session_id)
            if not session or not session.is_active:
                return None

            # Update context
            if merge and session.context:
                updated_context = {**session.context, **context_updates}
            else:
                updated_context = context_updates

            # Update session
            updated_session = await SessionService.update_session(
                db, session_id, {"context": updated_context}
            )

            self.logger.info(f"Updated context for session {session_id}")
            return updated_session

        except Exception as e:
            self.logger.error(
                f"Failed to update context for session {session_id}: {str(e)}"
            )
            raise

    async def add_conversation_message(
        self,
        db: AsyncSession,
        session_id: UUID,
        message: Dict[str, Any],
    ) -> Optional[Session]:
        """
        Add a message to the conversation history.

        Args:
            db: Database session
            session_id: Session ID
            message: Message data to add

        Returns:
            Updated session object
        """
        try:
            session = await SessionService.get_session_by_id(db, session_id)
            if not session or not session.is_active:
                return None

            # Add timestamp to message
            message["timestamp"] = datetime.utcnow().isoformat()

            # Update conversation history
            conversation_history = session.conversation_history or []
            conversation_history.append(message)

            # Limit conversation history size (keep last 50 messages)
            if len(conversation_history) > 50:
                conversation_history = conversation_history[-50:]

            # Update session
            updated_session = await SessionService.update_session(
                db, session_id, {"conversation_history": conversation_history}
            )

            self.logger.info(f"Added message to session {session_id}")
            return updated_session

        except Exception as e:
            self.logger.error(
                f"Failed to add message to session {session_id}: {str(e)}"
            )
            raise

    async def switch_channel(
        self,
        db: AsyncSession,
        user_id: UUID,
        from_channel: str,
        to_channel: str,
        context_transfer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Session]:
        """
        Handle cross-channel session continuity.

        Args:
            db: Database session
            user_id: User ID
            from_channel: Source channel
            to_channel: Target channel
            context_transfer: Additional context to transfer

        Returns:
            Session object for the target channel
        """
        try:
            # Get existing session from source channel
            source_session = await SessionService.get_active_session_by_user(
                db, user_id, from_channel
            )

            # Get or create session for target channel
            target_session = await SessionService.get_active_session_by_user(
                db, user_id, to_channel
            )

            if not target_session:
                # Create new session for target channel
                initial_context = {}

                # Transfer context from source session if available
                if source_session and source_session.context:
                    initial_context.update(source_session.context)

                # Add any additional context
                if context_transfer:
                    initial_context.update(context_transfer)

                target_session = await self.create_session(
                    db, user_id, to_channel, initial_context
                )

                self.logger.info(
                    f"Created new session {target_session.id} for channel switch "
                    f"from {from_channel} to {to_channel}"
                )
            else:
                # Update existing target session with transferred context
                if source_session and source_session.context:
                    context_updates = source_session.context.copy()
                    if context_transfer:
                        context_updates.update(context_transfer)

                    target_session = await self.update_session_context(
                        db, target_session.id, context_updates
                    )

                self.logger.info(
                    f"Updated existing session {target_session.id} for channel switch "
                    f"from {from_channel} to {to_channel}"
                )

            return target_session

        except Exception as e:
            self.logger.error(
                f"Failed to switch channel from {from_channel} to {to_channel} "
                f"for user {user_id}: {str(e)}"
            )
            raise

    async def update_session_activity(self, db: AsyncSession, session_id: UUID) -> bool:
        """
        Update session last activity timestamp.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            True if updated successfully
        """
        try:
            from datetime import timezone

            current_time = datetime.utcnow().replace(tzinfo=timezone.utc)

            updated_session = await SessionService.update_session(
                db, session_id, {"last_activity": current_time}
            )
            return updated_session is not None

        except Exception as e:
            self.logger.error(
                f"Failed to update activity for session {session_id}: {str(e)}"
            )
            return False

    async def deactivate_session(self, db: AsyncSession, session_id: UUID) -> bool:
        """
        Deactivate a session.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            True if deactivated successfully
        """
        try:
            result = await SessionService.deactivate_session(db, session_id)
            if result:
                self.logger.info(f"Deactivated session {session_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to deactivate session {session_id}: {str(e)}")
            return False

    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """
        Clean up expired and inactive sessions.

        Args:
            db: Database session

        Returns:
            Number of sessions cleaned up
        """
        try:
            # Clean up inactive sessions older than timeout period
            cleaned_count = await SessionService.cleanup_inactive_sessions(
                db, self.session_timeout_hours
            )

            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired sessions")

            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0

    async def get_user_sessions(
        self, db: AsyncSession, user_id: UUID, active_only: bool = True
    ) -> List[Session]:
        """
        Get all sessions for a user.

        Args:
            db: Database session
            user_id: User ID
            active_only: Whether to return only active sessions

        Returns:
            List of session objects
        """
        try:
            from sqlalchemy import select
            from app.models import Session

            query = select(Session).where(Session.user_id == user_id)

            if active_only:
                query = query.where(Session.is_active == True)

            result = await db.execute(query.order_by(Session.last_activity.desc()))
            sessions = list(result.scalars().all())

            # Filter out expired sessions
            if active_only:
                active_sessions = []
                for session in sessions:
                    if not self._is_session_expired(session):
                        active_sessions.append(session)
                    else:
                        # Deactivate expired session
                        await self.deactivate_session(db, session.id)

                return active_sessions

            return sessions

        except Exception as e:
            self.logger.error(f"Failed to get sessions for user {user_id}: {str(e)}")
            return []

    def _is_session_expired(self, session: Session) -> bool:
        """
        Check if a session has expired.

        Args:
            session: Session object

        Returns:
            True if session has expired
        """
        if not session.last_activity:
            return True

        from datetime import timezone

        # Ensure we're working with timezone-aware datetimes
        current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        last_activity = session.last_activity

        # If last_activity is timezone-naive, assume it's UTC
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)

        expiry_time = last_activity + timedelta(hours=self.session_timeout_hours)
        return current_time > expiry_time

    async def get_session_summary(
        self, db: AsyncSession, session_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get a summary of session information.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            Session summary dictionary
        """
        try:
            session = await SessionService.get_session_by_id(db, session_id)
            if not session:
                return None

            return {
                "session_id": str(session.id),
                "user_id": str(session.user_id),
                "channel": session.channel,
                "is_active": session.is_active,
                "last_activity": (
                    session.last_activity.isoformat() if session.last_activity else None
                ),
                "created_at": (
                    session.created_at.isoformat() if session.created_at else None
                ),
                "context_keys": list(session.context.keys()) if session.context else [],
                "conversation_length": (
                    len(session.conversation_history)
                    if session.conversation_history
                    else 0
                ),
                "user_preferences": session.user_preferences or {},
                "is_expired": self._is_session_expired(session),
            }

        except Exception as e:
            self.logger.error(f"Failed to get session summary {session_id}: {str(e)}")
            return None


# Global session manager instance
session_manager = SessionManager()
