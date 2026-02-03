"""
Translation service for the AI-Driven Agri-Civic Intelligence Platform.

This service provides comprehensive translation capabilities with language detection,
caching, fallback mechanisms, and error handling for multilingual support.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json

from google.cloud import translate_v2 as translate
from google.api_core import exceptions as google_exceptions
import redis.asyncio as redis

from app.config import get_settings
from app.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class TranslationProvider(str, Enum):
    """Supported translation providers."""

    GOOGLE = "google"
    # Future providers can be added here
    # AZURE = "azure"
    # AWS = "aws"


class TranslationError(Exception):
    """Base exception for translation service errors."""

    pass


class TranslationProviderError(TranslationError):
    """Exception raised when a translation provider fails."""

    def __init__(self, provider: str, message: str, original_error: Exception = None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"Translation Provider {provider} error: {message}")


class LanguageDetectionError(TranslationError):
    """Exception raised when language detection fails."""

    pass


class UnsupportedLanguageError(TranslationError):
    """Exception raised when a language is not supported."""

    pass


@dataclass
class TranslationRequest:
    """Translation request data structure."""

    text: str
    target_language: str
    source_language: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationResponse:
    """Translation response data structure."""

    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    provider: str
    cached: bool
    response_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LanguageDetectionResponse:
    """Language detection response data structure."""

    detected_language: str
    confidence: float
    provider: str
    response_time: float
    timestamp: datetime


@dataclass
class TranslationMetrics:
    """Translation service metrics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    language_detection_requests: int = 0
    provider_usage: Dict[str, int] = field(default_factory=dict)
    language_usage: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    average_response_time: float = 0.0


class GoogleTranslateClient:
    """Google Translate API client."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.google_translate_api_key:
            raise TranslationProviderError(
                "google", "Google Translate API key not configured"
            )

        self.client = translate.Client(api_key=self.settings.google_translate_api_key)

        # Language code mapping for better compatibility
        self.language_mapping = {
            "hi": "hi",  # Hindi
            "bn": "bn",  # Bengali
            "te": "te",  # Telugu
            "ta": "ta",  # Tamil
            "mr": "mr",  # Marathi
            "gu": "gu",  # Gujarati
            "kn": "kn",  # Kannada
            "ml": "ml",  # Malayalam
            "or": "or",  # Odia
            "en": "en",  # English
        }

    def _normalize_language_code(self, lang_code: str) -> str:
        """Normalize language code to Google Translate format."""
        return self.language_mapping.get(lang_code.lower(), lang_code.lower())

    async def detect_language(self, text: str) -> LanguageDetectionResponse:
        """Detect language of the given text."""
        start_time = time.time()

        try:
            # Run in thread pool since Google client is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.client.detect_language, text)

            response_time = time.time() - start_time

            return LanguageDetectionResponse(
                detected_language=result["language"],
                confidence=result["confidence"],
                provider=TranslationProvider.GOOGLE.value,
                response_time=response_time,
                timestamp=datetime.now(),
            )

        except google_exceptions.GoogleAPIError as e:
            raise TranslationProviderError(
                "google", f"Language detection failed: {str(e)}", e
            )
        except Exception as e:
            raise LanguageDetectionError(
                f"Unexpected error in language detection: {str(e)}"
            )

    async def translate_text(self, request: TranslationRequest) -> TranslationResponse:
        """Translate text using Google Translate API."""
        start_time = time.time()

        try:
            # Normalize language codes
            target_lang = self._normalize_language_code(request.target_language)
            source_lang = None
            if request.source_language:
                source_lang = self._normalize_language_code(request.source_language)

            # Prepare translation parameters
            translate_params = {"values": request.text, "target_language": target_lang}

            if source_lang:
                translate_params["source_language"] = source_lang

            # Run in thread pool since Google client is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self.client.translate(**translate_params)
            )

            response_time = time.time() - start_time

            # Handle both single and batch results
            if isinstance(result, list):
                result = result[0]

            return TranslationResponse(
                translated_text=result["translatedText"],
                source_language=result.get(
                    "detectedSourceLanguage", source_lang or "unknown"
                ),
                target_language=target_lang,
                confidence=1.0,  # Google doesn't provide confidence for translation
                provider=TranslationProvider.GOOGLE.value,
                cached=False,
                response_time=response_time,
                timestamp=datetime.now(),
                metadata=request.metadata,
            )

        except google_exceptions.GoogleAPIError as e:
            raise TranslationProviderError("google", f"Translation failed: {str(e)}", e)
        except Exception as e:
            raise TranslationError(f"Unexpected error in translation: {str(e)}")


class TranslationService:
    """
    Comprehensive translation service with caching, fallback mechanisms, and monitoring.

    Features:
    - Google Translate API integration
    - Language detection with confidence scoring
    - Redis-based caching for translation results
    - Fallback mechanisms for service failures
    - Comprehensive error handling and retry logic
    - Request/response monitoring and metrics
    - Support for all major Indian languages
    """

    def __init__(self):
        self.settings = get_settings()
        self.metrics = TranslationMetrics()
        self.clients: Dict[str, Any] = {}
        self.redis_client: Optional[redis.Redis] = None

        # Initialize clients and cache
        self._initialize_clients()
        self._initialize_cache()

        # Cache configuration
        self.cache_ttl = 86400  # 24 hours
        self.cache_prefix = "translation:"

        # Fallback responses for common phrases
        self.fallback_translations = {
            "en": {
                "hello": {"hi": "नमस्ते", "bn": "নমস্কার", "te": "నమస్కారం"},
                "thank you": {"hi": "धन्यवाद", "bn": "ধন্যবাদ", "te": "ధన్యవాదాలు"},
                "yes": {"hi": "हाँ", "bn": "হ্যাঁ", "te": "అవును"},
                "no": {"hi": "नहीं", "bn": "না", "te": "లేదు"},
            }
        }

    def _initialize_clients(self):
        """Initialize translation clients."""
        try:
            self.clients[TranslationProvider.GOOGLE.value] = GoogleTranslateClient()
            logger.info("Google Translate client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Translate client: {e}")

    async def _initialize_cache(self):
        """Initialize Redis cache connection."""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None

    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        # Create hash of text to handle long texts
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"{self.cache_prefix}{source_lang}:{target_lang}:{text_hash}"

    async def _get_cached_translation(
        self, text: str, source_lang: str, target_lang: str
    ) -> Optional[TranslationResponse]:
        """Get cached translation if available."""
        if not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(text, source_lang, target_lang)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                self.metrics.cache_hits += 1

                return TranslationResponse(
                    translated_text=data["translated_text"],
                    source_language=data["source_language"],
                    target_language=data["target_language"],
                    confidence=data["confidence"],
                    provider=data["provider"],
                    cached=True,
                    response_time=0.0,  # Cached response
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    metadata=data.get("metadata", {}),
                )
            else:
                self.metrics.cache_misses += 1
                return None

        except Exception as e:
            logger.warning(f"Failed to get cached translation: {e}")
            return None

    async def _cache_translation(
        self, response: TranslationResponse, original_text: str
    ):
        """Cache translation response."""
        if not self.redis_client:
            return

        try:
            cache_key = self._generate_cache_key(
                original_text, response.source_language, response.target_language
            )

            cache_data = {
                "translated_text": response.translated_text,
                "source_language": response.source_language,
                "target_language": response.target_language,
                "confidence": response.confidence,
                "provider": response.provider,
                "timestamp": response.timestamp.isoformat(),
                "metadata": response.metadata,
            }

            await self.redis_client.setex(
                cache_key, self.cache_ttl, json.dumps(cache_data)
            )

        except Exception as e:
            logger.warning(f"Failed to cache translation: {e}")

    def _get_fallback_translation(
        self, text: str, source_lang: str, target_lang: str
    ) -> Optional[str]:
        """Get fallback translation for common phrases."""
        text_lower = text.lower().strip()

        fallback_dict = self.fallback_translations.get(source_lang, {})
        phrase_translations = fallback_dict.get(text_lower, {})

        return phrase_translations.get(target_lang)

    def _is_supported_language(self, lang_code: str) -> bool:
        """Check if language is supported."""
        return lang_code.lower() in self.settings.supported_languages

    async def detect_language(self, text: str) -> LanguageDetectionResponse:
        """
        Detect the language of the given text.

        Args:
            text: Text to analyze for language detection

        Returns:
            LanguageDetectionResponse with detected language and confidence

        Raises:
            LanguageDetectionError: If language detection fails
        """
        if not text or not text.strip():
            raise LanguageDetectionError("Empty text provided for language detection")

        self.metrics.language_detection_requests += 1

        # Try Google Translate client
        if TranslationProvider.GOOGLE.value in self.clients:
            try:
                client = self.clients[TranslationProvider.GOOGLE.value]
                response = await client.detect_language(text)

                logger.info(
                    f"Language detected: {response.detected_language} "
                    f"(confidence: {response.confidence:.2f})"
                )

                return response

            except Exception as e:
                logger.error(f"Language detection failed: {e}")
                raise LanguageDetectionError(f"Language detection failed: {str(e)}")

        raise LanguageDetectionError("No language detection providers available")

    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        use_cache: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranslationResponse:
        """
        Translate text from source language to target language.

        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'hi', 'en')
            source_language: Source language code (auto-detected if None)
            use_cache: Whether to use cached translations
            metadata: Additional metadata to include in response

        Returns:
            TranslationResponse with translated text and metadata

        Raises:
            TranslationError: If translation fails
            UnsupportedLanguageError: If language is not supported
        """
        if not text or not text.strip():
            raise TranslationError("Empty text provided for translation")

        # Validate target language
        if not self._is_supported_language(target_language):
            raise UnsupportedLanguageError(
                f"Target language '{target_language}' not supported"
            )

        # If source and target are the same, return original text
        if source_language and source_language.lower() == target_language.lower():
            return TranslationResponse(
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=1.0,
                provider="passthrough",
                cached=False,
                response_time=0.0,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

        self.metrics.total_requests += 1

        # Auto-detect source language if not provided
        if not source_language:
            try:
                detection_response = await self.detect_language(text)
                source_language = detection_response.detected_language
                logger.info(f"Auto-detected source language: {source_language}")
            except Exception as e:
                logger.warning(f"Language detection failed, assuming English: {e}")
                source_language = "en"

        # Validate source language
        if not self._is_supported_language(source_language):
            logger.warning(
                f"Source language '{source_language}' not supported, assuming English"
            )
            source_language = "en"

        # Check cache first
        if use_cache:
            cached_response = await self._get_cached_translation(
                text, source_language, target_language
            )
            if cached_response:
                logger.info("Using cached translation")
                return cached_response

        # Try fallback translation for common phrases
        fallback_text = self._get_fallback_translation(
            text, source_language, target_language
        )
        if fallback_text:
            logger.info("Using fallback translation for common phrase")
            response = TranslationResponse(
                translated_text=fallback_text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.9,
                provider="fallback",
                cached=False,
                response_time=0.0,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            # Cache the fallback translation
            if use_cache:
                await self._cache_translation(response, text)

            self.metrics.successful_requests += 1
            return response

        # Try Google Translate
        if TranslationProvider.GOOGLE.value in self.clients:
            try:
                client = self.clients[TranslationProvider.GOOGLE.value]
                request = TranslationRequest(
                    text=text,
                    target_language=target_language,
                    source_language=source_language,
                    metadata=metadata or {},
                )

                response = await client.translate_text(request)

                # Cache successful translation
                if use_cache:
                    await self._cache_translation(response, text)

                # Update metrics
                self.metrics.successful_requests += 1
                self.metrics.provider_usage[response.provider] = (
                    self.metrics.provider_usage.get(response.provider, 0) + 1
                )
                self.metrics.language_usage[f"{source_language}->{target_language}"] = (
                    self.metrics.language_usage.get(
                        f"{source_language}->{target_language}", 0
                    )
                    + 1
                )

                # Update average response time
                total_successful = self.metrics.successful_requests
                self.metrics.average_response_time = (
                    self.metrics.average_response_time * (total_successful - 1)
                    + response.response_time
                ) / total_successful

                logger.info(
                    f"Translation successful: {source_language} -> {target_language} "
                    f"(response time: {response.response_time:.2f}s)"
                )

                return response

            except Exception as e:
                error_type = type(e).__name__
                self.metrics.error_counts[error_type] = (
                    self.metrics.error_counts.get(error_type, 0) + 1
                )
                logger.error(f"Google Translate failed: {e}")

                # If it's a specific error we can handle, re-raise it
                if isinstance(e, (TranslationError, UnsupportedLanguageError)):
                    raise e

        # All translation methods failed
        self.metrics.failed_requests += 1
        raise TranslationError(
            f"Translation failed for {source_language} -> {target_language}. "
            "No translation providers available or all providers failed."
        )

    async def batch_translate(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None,
        use_cache: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[TranslationResponse]:
        """
        Translate multiple texts in batch.

        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code (auto-detected if None)
            use_cache: Whether to use cached translations
            metadata: Additional metadata to include in responses

        Returns:
            List of TranslationResponse objects
        """
        if not texts:
            return []

        # Process translations concurrently
        tasks = [
            self.translate(
                text=text,
                target_language=target_language,
                source_language=source_language,
                use_cache=use_cache,
                metadata=metadata,
            )
            for text in texts
        ]

        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle any exceptions in the results
            results = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"Batch translation failed for text {i}: {response}")
                    # Create error response
                    error_response = TranslationResponse(
                        translated_text=texts[i],  # Return original text on error
                        source_language=source_language or "unknown",
                        target_language=target_language,
                        confidence=0.0,
                        provider="error",
                        cached=False,
                        response_time=0.0,
                        timestamp=datetime.now(),
                        metadata={"error": str(response)},
                    )
                    results.append(error_response)
                else:
                    results.append(response)

            return results

        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            raise TranslationError(f"Batch translation failed: {str(e)}")

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return self.settings.supported_languages.copy()

    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics."""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / max(self.metrics.total_requests, 1)
            ),
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cache_hit_rate": (
                self.metrics.cache_hits
                / max(self.metrics.cache_hits + self.metrics.cache_misses, 1)
            ),
            "language_detection_requests": self.metrics.language_detection_requests,
            "provider_usage": self.metrics.provider_usage,
            "language_usage": self.metrics.language_usage,
            "error_counts": self.metrics.error_counts,
            "average_response_time": self.metrics.average_response_time,
            "available_providers": list(self.clients.keys()),
            "supported_languages": self.get_supported_languages(),
        }

    def reset_metrics(self):
        """Reset service metrics."""
        self.metrics = TranslationMetrics()
        logger.info("Translation service metrics reset")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on translation service."""
        health_status = {
            "status": "healthy",
            "providers": {},
            "cache": {"status": "unknown"},
            "timestamp": datetime.now().isoformat(),
        }

        # Test translation providers
        test_text = "Hello, this is a health check."

        for provider_name, client in self.clients.items():
            try:
                if provider_name == TranslationProvider.GOOGLE.value:
                    # Test language detection
                    detection_response = await client.detect_language(test_text)

                    # Test translation
                    request = TranslationRequest(
                        text=test_text, target_language="hi", source_language="en"
                    )
                    translation_response = await client.translate_text(request)

                    health_status["providers"][provider_name] = {
                        "status": "healthy",
                        "healthy": True,
                        "detection_response_time": detection_response.response_time,
                        "translation_response_time": translation_response.response_time,
                    }

            except Exception as e:
                health_status["providers"][provider_name] = {
                    "status": "unhealthy",
                    "healthy": False,
                    "error": str(e),
                }
                health_status["status"] = "degraded"

        # Test cache
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health_status["cache"] = {"status": "healthy", "healthy": True}
            except Exception as e:
                health_status["cache"] = {
                    "status": "unhealthy",
                    "healthy": False,
                    "error": str(e),
                }
        else:
            health_status["cache"] = {"status": "not_configured", "healthy": False}

        # Overall status
        if not any(
            p.get("healthy", False) for p in health_status["providers"].values()
        ):
            health_status["status"] = "unhealthy"

        return health_status


# Global instance
translation_service = TranslationService()
