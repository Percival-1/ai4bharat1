"""
Translation API endpoints for the AI-Driven Agri-Civic Intelligence Platform.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.translation import (
    translation_service,
    TranslationError,
    LanguageDetectionError,
    UnsupportedLanguageError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])


class TranslationRequest(BaseModel):
    """Translation request model."""

    text: str = Field(..., description="Text to translate", min_length=1)
    target_language: str = Field(
        ..., description="Target language code (e.g., 'hi', 'en')"
    )
    source_language: Optional[str] = Field(
        None, description="Source language code (auto-detected if not provided)"
    )
    use_cache: bool = Field(True, description="Whether to use cached translations")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchTranslationRequest(BaseModel):
    """Batch translation request model."""

    texts: List[str] = Field(..., description="List of texts to translate", min_items=1)
    target_language: str = Field(..., description="Target language code")
    source_language: Optional[str] = Field(
        None, description="Source language code (auto-detected if not provided)"
    )
    use_cache: bool = Field(True, description="Whether to use cached translations")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class LanguageDetectionRequest(BaseModel):
    """Language detection request model."""

    text: str = Field(
        ..., description="Text to analyze for language detection", min_length=1
    )


class TranslationResponse(BaseModel):
    """Translation response model."""

    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    provider: str
    cached: bool
    response_time: float
    timestamp: str
    metadata: Dict[str, Any] = {}


class LanguageDetectionResponse(BaseModel):
    """Language detection response model."""

    detected_language: str
    confidence: float
    provider: str
    response_time: float
    timestamp: str


class SupportedLanguagesResponse(BaseModel):
    """Supported languages response model."""

    languages: List[str]
    total_count: int


class TranslationMetricsResponse(BaseModel):
    """Translation metrics response model."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    language_detection_requests: int
    provider_usage: Dict[str, int]
    language_usage: Dict[str, int]
    error_counts: Dict[str, int]
    average_response_time: float
    available_providers: List[str]
    supported_languages: List[str]


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text from source language to target language.

    This endpoint provides comprehensive translation capabilities with:
    - Automatic language detection if source language not provided
    - Caching for improved performance
    - Fallback mechanisms for common phrases
    - Support for all major Indian languages
    """
    try:
        response = await translation_service.translate(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language,
            use_cache=request.use_cache,
            metadata=request.metadata,
        )

        return TranslationResponse(
            translated_text=response.translated_text,
            source_language=response.source_language,
            target_language=response.target_language,
            confidence=response.confidence,
            provider=response.provider,
            cached=response.cached,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
            metadata=response.metadata,
        )

    except UnsupportedLanguageError as e:
        logger.error(f"Unsupported language error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except TranslationError as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in translation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/translate/batch", response_model=List[TranslationResponse])
async def translate_batch(request: BatchTranslationRequest):
    """
    Translate multiple texts in batch for improved efficiency.

    This endpoint processes multiple translation requests concurrently,
    providing better performance for bulk translation operations.
    """
    try:
        responses = await translation_service.batch_translate(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language,
            use_cache=request.use_cache,
            metadata=request.metadata,
        )

        return [
            TranslationResponse(
                translated_text=response.translated_text,
                source_language=response.source_language,
                target_language=response.target_language,
                confidence=response.confidence,
                provider=response.provider,
                cached=response.cached,
                response_time=response.response_time,
                timestamp=response.timestamp.isoformat(),
                metadata=response.metadata,
            )
            for response in responses
        ]

    except UnsupportedLanguageError as e:
        logger.error(f"Unsupported language error in batch translation: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except TranslationError as e:
        logger.error(f"Translation error in batch translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in batch translation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """
    Detect the language of the provided text.

    This endpoint uses advanced language detection algorithms to identify
    the language of input text with confidence scoring.
    """
    try:
        response = await translation_service.detect_language(request.text)

        return LanguageDetectionResponse(
            detected_language=response.detected_language,
            confidence=response.confidence,
            provider=response.provider,
            response_time=response.response_time,
            timestamp=response.timestamp.isoformat(),
        )

    except LanguageDetectionError as e:
        logger.error(f"Language detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/supported-languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages():
    """
    Get list of supported language codes.

    Returns all language codes that are supported by the translation service,
    including major Indian languages and English.
    """
    try:
        languages = translation_service.get_supported_languages()

        return SupportedLanguagesResponse(
            languages=languages, total_count=len(languages)
        )

    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics", response_model=TranslationMetricsResponse)
async def get_translation_metrics():
    """
    Get translation service metrics and statistics.

    Provides comprehensive metrics including:
    - Request counts and success rates
    - Cache performance statistics
    - Provider usage statistics
    - Language usage patterns
    - Error counts and response times
    """
    try:
        metrics = translation_service.get_metrics()

        return TranslationMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Error getting translation metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/metrics/reset")
async def reset_translation_metrics():
    """
    Reset translation service metrics.

    This endpoint resets all accumulated metrics and statistics.
    Useful for testing or periodic metric resets.
    """
    try:
        translation_service.reset_metrics()
        return {"message": "Translation metrics reset successfully"}

    except Exception as e:
        logger.error(f"Error resetting translation metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def translation_health_check():
    """
    Perform health check on translation service.

    Tests all translation providers and cache connectivity to ensure
    the service is functioning properly.
    """
    try:
        health_status = await translation_service.health_check()

        # Return appropriate HTTP status based on health
        if health_status["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=health_status)
        elif health_status["status"] == "degraded":
            # Return 200 but indicate degraded status
            return {**health_status, "warning": "Service is running in degraded mode"}

        return health_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in translation health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# Convenience endpoints for common translation pairs
@router.post("/translate/to-english")
async def translate_to_english(
    text: str = Query(..., description="Text to translate to English"),
    source_language: Optional[str] = Query(
        None, description="Source language (auto-detected if not provided)"
    ),
    use_cache: bool = Query(True, description="Whether to use cached translations"),
):
    """Convenience endpoint to translate any text to English."""
    request = TranslationRequest(
        text=text,
        target_language="en",
        source_language=source_language,
        use_cache=use_cache,
    )
    return await translate_text(request)


@router.post("/translate/from-english")
async def translate_from_english(
    text: str = Query(..., description="English text to translate"),
    target_language: str = Query(..., description="Target language code"),
    use_cache: bool = Query(True, description="Whether to use cached translations"),
):
    """Convenience endpoint to translate English text to any supported language."""
    request = TranslationRequest(
        text=text,
        target_language=target_language,
        source_language="en",
        use_cache=use_cache,
    )
    return await translate_text(request)
