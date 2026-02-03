"""
LLM API endpoints for the AI-Driven Agri-Civic Intelligence Platform.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.llm_service import llm_service, LLMError
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])


class LLMGenerateRequest(BaseModel):
    """Request model for LLM generation."""

    prompt: str = Field(..., description="The user prompt")
    system_message: Optional[str] = Field(None, description="Optional system message")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for response")
    temperature: Optional[float] = Field(
        None, description="Response randomness (0.0-1.0)"
    )
    model: Optional[str] = Field(None, description="Specific model to use")
    provider: Optional[str] = Field(None, description="Specific provider to use")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class LLMGenerateResponse(BaseModel):
    """Response model for LLM generation."""

    content: str = Field(..., description="Generated content")
    provider: str = Field(..., description="Provider used")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Number of tokens used")
    response_time: float = Field(..., description="Response time in seconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


class LLMMetricsResponse(BaseModel):
    """Response model for LLM metrics."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    total_tokens_used: int
    average_response_time: float
    provider_usage: Dict[str, int]
    error_counts: Dict[str, int]
    circuit_breaker_state: Dict[str, Dict[str, Any]]
    available_providers: list


class LLMHealthResponse(BaseModel):
    """Response model for LLM health check."""

    status: str
    providers: Dict[str, Dict[str, Any]]
    timestamp: str


@router.post("/generate", response_model=LLMGenerateResponse)
async def generate_response(request: LLMGenerateRequest):
    """
    Generate response using LLM service.

    This endpoint provides access to the LLM service with automatic failover,
    retry mechanisms, and comprehensive error handling.
    """
    try:
        logger.info(
            f"LLM generation request: provider={request.provider}, model={request.model}"
        )

        response = await llm_service.generate_response(
            prompt=request.prompt,
            system_message=request.system_message,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            model=request.model,
            provider=request.provider,
            metadata=request.metadata,
        )

        return LLMGenerateResponse(
            content=response.content,
            provider=response.provider,
            model=response.model,
            tokens_used=response.tokens_used,
            response_time=response.response_time,
            metadata=response.metadata,
        )

    except LLMError as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in LLM generation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics", response_model=LLMMetricsResponse)
async def get_metrics():
    """
    Get LLM service metrics.

    Returns comprehensive metrics including request counts, success rates,
    token usage, response times, and provider statistics.
    """
    try:
        metrics = llm_service.get_metrics()
        return LLMMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Error retrieving LLM metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.post("/metrics/reset")
async def reset_metrics():
    """
    Reset LLM service metrics.

    Clears all accumulated metrics and resets counters to zero.
    """
    try:
        llm_service.reset_metrics()
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting LLM metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset metrics")


@router.get("/health", response_model=LLMHealthResponse)
async def health_check():
    """
    Perform health check on LLM service.

    Tests connectivity and functionality of all configured LLM providers.
    Returns detailed status information for each provider.
    """
    try:
        health_status = await llm_service.health_check()
        return LLMHealthResponse(**health_status)
    except Exception as e:
        logger.error(f"Error in LLM health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/providers")
async def get_available_providers():
    """
    Get list of available LLM providers.

    Returns information about configured providers and their current status.
    """
    try:
        metrics = llm_service.get_metrics()
        return {
            "available_providers": metrics["available_providers"],
            "circuit_breaker_state": metrics["circuit_breaker_state"],
            "provider_usage": metrics["provider_usage"],
        }
    except Exception as e:
        logger.error(f"Error retrieving provider information: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve provider information"
        )
