"""
Health check endpoints for the AI-Driven Agri-Civic Intelligence Platform.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""

    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, Any]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        environment=settings.environment,
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
)
async def detailed_health_check() -> DetailedHealthResponse:
    """Detailed health check endpoint with service status."""
    # TODO: Add actual service health checks
    services = {
        "database": {"status": "unknown", "message": "Not implemented"},
        "redis": {"status": "unknown", "message": "Not implemented"},
        "external_apis": {"status": "unknown", "message": "Not implemented"},
    }

    return DetailedHealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        environment=settings.environment,
        services=services,
    )
