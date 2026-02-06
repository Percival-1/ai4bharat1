"""
Session Management API endpoints.

Provides REST API endpoints for session lifecycle management,
context persistence, and cross-channel continuity.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.session_manager import session_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class SessionCreateRequest(BaseModel):
    """Request model for creating a new session."""

    user_id: UUID = Field(..., description="User ID")
    channel: str = Field(
        ..., description="Communication channel", pattern="^(voice|sms|chat|ivr)$"
    )
    initial_context: Optional[Dict[str, Any]] = Field(
        None, description="Initial context data"
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        None, description="User preferences"
    )


class SessionResponse(BaseModel):
    """Response model for session data."""

    session_id: UUID = Field(..., description="Session ID")
    user_id: UUID = Field(..., description="User ID")
    channel: str = Field(..., description="Communication channel")
    is_active: bool = Field(..., description="Whether session is active")
    context: Optional[Dict[str, Any]] = Field(None, description="Session context")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        None, description="Conversation history"
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        None, description="User preferences"
    )
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class SessionSummaryResponse(BaseModel):
    """Response model for session summary."""

    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    channel: str = Field(..., description="Communication channel")
    is_active: bool = Field(..., description="Whether session is active")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    context_keys: List[str] = Field(..., description="Available context keys")
    conversation_length: int = Field(
        ..., description="Number of messages in conversation"
    )
    user_preferences: Dict[str, Any] = Field(..., description="User preferences")
    is_expired: bool = Field(..., description="Whether session has expired")


class ContextUpdateRequest(BaseModel):
    """Request model for updating session context."""

    context_updates: Dict[str, Any] = Field(..., description="Context data to update")
    merge: bool = Field(True, description="Whether to merge with existing context")


class MessageRequest(BaseModel):
    """Request model for adding a conversation message."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional message metadata"
    )


class ChannelSwitchRequest(BaseModel):
    """Request model for channel switching."""

    user_id: UUID = Field(..., description="User ID")
    from_channel: str = Field(..., description="Source channel")
    to_channel: str = Field(..., description="Target channel")
    context_transfer: Optional[Dict[str, Any]] = Field(
        None, description="Additional context to transfer"
    )


class CleanupResponse(BaseModel):
    """Response model for cleanup operations."""

    cleaned_sessions: int = Field(..., description="Number of sessions cleaned up")
    message: str = Field(..., description="Cleanup result message")


@router.post(
    "/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    request: SessionCreateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Create a new session for a user.

    Creates a new session with the specified channel and initial context.
    If a session already exists for the user and channel, returns the existing session.
    """
    try:
        session = await session_manager.get_or_create_session(
            db=db,
            user_id=request.user_id,
            channel=request.channel,
            initial_context=request.initial_context,
        )

        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            channel=session.channel,
            is_active=session.is_active,
            context=session.context,
            conversation_history=session.conversation_history,
            user_preferences=session.user_preferences,
            last_activity=(
                session.last_activity.isoformat() if session.last_activity else None
            ),
            created_at=session.created_at.isoformat() if session.created_at else None,
        )

    except ValueError as e:
        logger.error(f"Invalid request for session creation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get session by ID.

    Retrieves session information and updates the last activity timestamp.
    Returns 404 if session not found or expired.
    """
    try:
        session = await session_manager.get_session(db, session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired",
            )

        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            channel=session.channel,
            is_active=session.is_active,
            context=session.context,
            conversation_history=session.conversation_history,
            user_preferences=session.user_preferences,
            last_activity=(
                session.last_activity.isoformat() if session.last_activity else None
            ),
            created_at=session.created_at.isoformat() if session.created_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session",
        )


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get session summary.

    Returns a summary of session information without full context and conversation history.
    """
    try:
        summary = await session_manager.get_session_summary(db, session_id)

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        return SessionSummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session summary {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session summary",
        )


@router.put("/sessions/{session_id}/context", response_model=SessionResponse)
async def update_session_context(
    session_id: UUID, request: ContextUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Update session context.

    Updates the session context with the provided data.
    Can either merge with existing context or replace it entirely.
    """
    try:
        session = await session_manager.update_session_context(
            db=db,
            session_id=session_id,
            context_updates=request.context_updates,
            merge=request.merge,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or inactive",
            )

        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            channel=session.channel,
            is_active=session.is_active,
            context=session.context,
            conversation_history=session.conversation_history,
            user_preferences=session.user_preferences,
            last_activity=(
                session.last_activity.isoformat() if session.last_activity else None
            ),
            created_at=session.created_at.isoformat() if session.created_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update context for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session context",
        )


@router.post("/sessions/{session_id}/messages", response_model=SessionResponse)
async def add_conversation_message(
    session_id: UUID, request: MessageRequest, db: AsyncSession = Depends(get_db)
):
    """
    Add a message to the conversation history.

    Adds a new message to the session's conversation history.
    Automatically limits history to the last 50 messages.
    """
    try:
        message_data = {
            "role": request.role,
            "content": request.content,
            "metadata": request.metadata or {},
        }

        session = await session_manager.add_conversation_message(
            db=db, session_id=session_id, message=message_data
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or inactive",
            )

        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            channel=session.channel,
            is_active=session.is_active,
            context=session.context,
            conversation_history=session.conversation_history,
            user_preferences=session.user_preferences,
            last_activity=(
                session.last_activity.isoformat() if session.last_activity else None
            ),
            created_at=session.created_at.isoformat() if session.created_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add conversation message",
        )


@router.post("/sessions/switch-channel", response_model=SessionResponse)
async def switch_channel(
    request: ChannelSwitchRequest, db: AsyncSession = Depends(get_db)
):
    """
    Handle cross-channel session continuity.

    Switches user session from one channel to another while preserving context.
    Creates a new session for the target channel if one doesn't exist.
    """
    try:
        session = await session_manager.switch_channel(
            db=db,
            user_id=request.user_id,
            from_channel=request.from_channel,
            to_channel=request.to_channel,
            context_transfer=request.context_transfer,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to switch channel",
            )

        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            channel=session.channel,
            is_active=session.is_active,
            context=session.context,
            conversation_history=session.conversation_history,
            user_preferences=session.user_preferences,
            last_activity=(
                session.last_activity.isoformat() if session.last_activity else None
            ),
            created_at=session.created_at.isoformat() if session.created_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch channel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch channel",
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Deactivate a session.

    Marks the session as inactive. The session data is preserved for audit purposes.
    """
    try:
        result = await session_manager.deactivate_session(db, session_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate session",
        )


@router.get("/users/{user_id}/sessions", response_model=List[SessionSummaryResponse])
async def get_user_sessions(
    user_id: UUID, active_only: bool = True, db: AsyncSession = Depends(get_db)
):
    """
    Get all sessions for a user.

    Returns a list of session summaries for the specified user.
    Can filter to show only active sessions or include all sessions.
    """
    try:
        sessions = await session_manager.get_user_sessions(
            db=db, user_id=user_id, active_only=active_only
        )

        summaries = []
        for session in sessions:
            summary = await session_manager.get_session_summary(db, session.id)
            if summary:
                summaries.append(SessionSummaryResponse(**summary))

        return summaries

    except Exception as e:
        logger.error(f"Failed to get sessions for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions",
        )


@router.post("/sessions/cleanup", response_model=CleanupResponse)
async def cleanup_expired_sessions(db: AsyncSession = Depends(get_db)):
    """
    Clean up expired sessions.

    Removes inactive sessions that have exceeded the timeout period.
    This endpoint can be called periodically for maintenance.
    """
    try:
        cleaned_count = await session_manager.cleanup_expired_sessions(db)

        return CleanupResponse(
            cleaned_sessions=cleaned_count,
            message=f"Successfully cleaned up {cleaned_count} expired sessions",
        )

    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired sessions",
        )


@router.put("/sessions/{session_id}/activity", status_code=status.HTTP_204_NO_CONTENT)
async def update_session_activity(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Update session activity timestamp.

    Updates the last activity timestamp for the session to prevent expiration.
    """
    try:
        result = await session_manager.update_session_activity(db, session_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update activity for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session activity",
        )
