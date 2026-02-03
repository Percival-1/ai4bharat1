"""
LLM service for the AI-Driven Agri-Civic Intelligence Platform.

This service provides a unified interface for interacting with multiple LLM providers
(OpenAI, Anthropic) with comprehensive error handling, retry mechanisms, and monitoring.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import openai
import anthropic
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.config import get_settings


# Configure logging
logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMError(Exception):
    """Base exception for LLM service errors."""

    pass


class LLMProviderError(LLMError):
    """Exception raised when a specific LLM provider fails."""

    def __init__(self, provider: str, message: str, original_error: Exception = None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"LLM Provider {provider} error: {message}")


class LLMTimeoutError(LLMError):
    """Exception raised when LLM request times out."""

    pass


class LLMRateLimitError(LLMError):
    """Exception raised when rate limit is exceeded."""

    pass


@dataclass
class LLMRequest:
    """LLM request data structure."""

    prompt: str
    system_message: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM response data structure."""

    content: str
    provider: str
    model: str
    tokens_used: int
    response_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMetrics:
    """LLM service metrics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    average_response_time: float = 0.0
    provider_usage: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)


class LLMClient:
    """Base class for LLM clients."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.settings = get_settings()

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM."""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI LLM client."""

    def __init__(self):
        super().__init__(LLMProvider.OPENAI)
        self.client = AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.llm_timeout_seconds,
        )

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API."""
        start_time = time.time()

        try:
            messages = []
            if request.system_message:
                messages.append({"role": "system", "content": request.system_message})
            messages.append({"role": "user", "content": request.prompt})

            response = await self.client.chat.completions.create(
                model=request.model or self.settings.llm_model,
                messages=messages,
                max_tokens=request.max_tokens or self.settings.llm_max_tokens,
                temperature=request.temperature or self.settings.llm_temperature,
            )

            response_time = time.time() - start_time

            return LLMResponse(
                content=response.choices[0].message.content,
                provider=self.provider.value,
                model=response.model,
                tokens_used=response.usage.total_tokens,
                response_time=response_time,
                timestamp=datetime.now(),
                metadata=request.metadata,
            )

        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {str(e)}")
        except openai.APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI request timeout: {str(e)}")
        except Exception as e:
            raise LLMProviderError("openai", str(e), e)


class AnthropicClient(LLMClient):
    """Anthropic LLM client."""

    def __init__(self):
        super().__init__(LLMProvider.ANTHROPIC)
        self.client = AsyncAnthropic(
            api_key=self.settings.anthropic_api_key,
            timeout=self.settings.llm_timeout_seconds,
        )

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic API."""
        start_time = time.time()

        try:
            # Map OpenAI model names to Anthropic equivalents
            model_mapping = {
                "gpt-3.5-turbo": "claude-3-haiku-20240307",
                "gpt-4": "claude-3-sonnet-20240229",
                "gpt-4-turbo": "claude-3-opus-20240229",
            }

            model = request.model or self.settings.llm_model
            anthropic_model = model_mapping.get(model, "claude-3-haiku-20240307")

            # Construct the prompt with system message if provided
            full_prompt = request.prompt
            if request.system_message:
                full_prompt = (
                    f"System: {request.system_message}\n\nHuman: {request.prompt}"
                )
            else:
                full_prompt = f"Human: {request.prompt}"

            response = await self.client.messages.create(
                model=anthropic_model,
                max_tokens=request.max_tokens or self.settings.llm_max_tokens,
                temperature=request.temperature or self.settings.llm_temperature,
                messages=[{"role": "user", "content": full_prompt}],
            )

            response_time = time.time() - start_time

            return LLMResponse(
                content=response.content[0].text,
                provider=self.provider.value,
                model=anthropic_model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                response_time=response_time,
                timestamp=datetime.now(),
                metadata=request.metadata,
            )

        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic rate limit exceeded: {str(e)}")
        except anthropic.APITimeoutError as e:
            raise LLMTimeoutError(f"Anthropic request timeout: {str(e)}")
        except Exception as e:
            raise LLMProviderError("anthropic", str(e), e)


class LLMService:
    """
    Comprehensive LLM service with multi-provider support, error handling, and monitoring.

    Features:
    - Multi-provider support (OpenAI, Anthropic)
    - Automatic failover between providers
    - Retry mechanisms with exponential backoff
    - Request/response logging and monitoring
    - API key rotation support
    - Circuit breaker pattern for resilience
    """

    def __init__(self):
        self.settings = get_settings()
        self.clients: Dict[str, LLMClient] = {}
        self.metrics = LLMMetrics()
        self.circuit_breaker_state: Dict[str, Dict[str, Any]] = {}

        # Initialize clients
        self._initialize_clients()

        # Initialize circuit breaker state
        for provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            self.circuit_breaker_state[provider.value] = {
                "failures": 0,
                "last_failure": None,
                "state": "closed",  # closed, open, half-open
            }

    def _initialize_clients(self):
        """Initialize LLM clients based on available API keys."""
        if self.settings.openai_api_key:
            try:
                self.clients[LLMProvider.OPENAI.value] = OpenAIClient()
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        if self.settings.anthropic_api_key:
            try:
                self.clients[LLMProvider.ANTHROPIC.value] = AnthropicClient()
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

        if not self.clients:
            logger.warning(
                "No LLM clients initialized. Please check API key configuration."
            )

    def _is_circuit_breaker_open(self, provider: str) -> bool:
        """Check if circuit breaker is open for a provider."""
        state = self.circuit_breaker_state.get(provider, {})

        if state.get("state") == "open":
            # Check if we should transition to half-open
            last_failure = state.get("last_failure")
            if last_failure and datetime.now() - last_failure > timedelta(minutes=5):
                state["state"] = "half-open"
                logger.info(f"Circuit breaker for {provider} transitioned to half-open")
                return False
            return True

        return False

    def _record_success(self, provider: str):
        """Record successful request for circuit breaker."""
        state = self.circuit_breaker_state.get(provider, {})
        state["failures"] = 0
        state["state"] = "closed"
        state["last_failure"] = None

    def _record_failure(self, provider: str):
        """Record failed request for circuit breaker."""
        state = self.circuit_breaker_state.get(provider, {})
        state["failures"] = state.get("failures", 0) + 1
        state["last_failure"] = datetime.now()

        # Open circuit breaker after 3 consecutive failures
        if state["failures"] >= 3:
            state["state"] = "open"
            logger.warning(
                f"Circuit breaker for {provider} opened due to consecutive failures"
            )

    async def _generate_with_retry(
        self, client: LLMClient, request: LLMRequest, max_retries: Optional[int] = None
    ) -> LLMResponse:
        """Generate response with retry logic."""
        max_retries = max_retries or self.settings.llm_max_retries
        retry_delay = self.settings.llm_retry_delay

        for attempt in range(max_retries + 1):
            try:
                response = await client.generate_response(request)
                self._record_success(client.provider.value)
                return response

            except (LLMTimeoutError, LLMRateLimitError) as e:
                if attempt == max_retries:
                    self._record_failure(client.provider.value)
                    raise e

                # Exponential backoff
                wait_time = retry_delay * (2**attempt)
                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {wait_time} seconds..."
                )
                await asyncio.sleep(wait_time)

            except LLMProviderError as e:
                self._record_failure(client.provider.value)
                raise e

    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Generate response using LLM with automatic failover and retry logic.

        Args:
            prompt: The user prompt
            system_message: Optional system message
            max_tokens: Maximum tokens for response
            temperature: Response randomness (0.0-1.0)
            model: Specific model to use
            provider: Specific provider to use
            metadata: Additional metadata to include in response

        Returns:
            LLMResponse object with generated content and metadata

        Raises:
            LLMError: If all providers fail or no providers are available
        """
        request = LLMRequest(
            prompt=prompt,
            system_message=system_message,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
            metadata=metadata or {},
        )

        # Update metrics
        self.metrics.total_requests += 1

        # Determine provider order
        if provider and provider in self.clients:
            provider_order = [provider]
        else:
            # Use primary provider first, then fallback
            provider_order = [
                self.settings.primary_llm_provider,
                self.settings.fallback_llm_provider,
            ]
            # Remove duplicates while preserving order
            provider_order = list(dict.fromkeys(provider_order))

        last_error = None

        for provider_name in provider_order:
            if provider_name not in self.clients:
                logger.warning(f"Provider {provider_name} not available")
                continue

            if self._is_circuit_breaker_open(provider_name):
                logger.warning(f"Circuit breaker open for {provider_name}, skipping")
                continue

            client = self.clients[provider_name]

            try:
                logger.info(f"Attempting LLM request with provider: {provider_name}")

                response = await self._generate_with_retry(client, request)

                # Update metrics
                self.metrics.successful_requests += 1
                self.metrics.total_tokens_used += response.tokens_used
                self.metrics.provider_usage[provider_name] = (
                    self.metrics.provider_usage.get(provider_name, 0) + 1
                )

                # Update average response time
                total_successful = self.metrics.successful_requests
                self.metrics.average_response_time = (
                    self.metrics.average_response_time * (total_successful - 1)
                    + response.response_time
                ) / total_successful

                logger.info(
                    f"LLM request successful with {provider_name}. "
                    f"Tokens: {response.tokens_used}, "
                    f"Response time: {response.response_time:.2f}s"
                )

                return response

            except LLMError as e:
                last_error = e
                error_type = type(e).__name__
                self.metrics.error_counts[error_type] = (
                    self.metrics.error_counts.get(error_type, 0) + 1
                )

                logger.error(f"LLM request failed with {provider_name}: {e}")
                continue

        # All providers failed
        self.metrics.failed_requests += 1

        if last_error:
            raise last_error
        else:
            raise LLMError("No LLM providers available or all providers failed")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics."""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / max(self.metrics.total_requests, 1)
            ),
            "total_tokens_used": self.metrics.total_tokens_used,
            "average_response_time": self.metrics.average_response_time,
            "provider_usage": self.metrics.provider_usage,
            "error_counts": self.metrics.error_counts,
            "circuit_breaker_state": self.circuit_breaker_state,
            "available_providers": list(self.clients.keys()),
        }

    def reset_metrics(self):
        """Reset service metrics."""
        self.metrics = LLMMetrics()
        logger.info("LLM service metrics reset")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers."""
        health_status = {
            "status": "healthy",
            "providers": {},
            "timestamp": datetime.now().isoformat(),
        }

        test_request = LLMRequest(
            prompt="Hello, this is a health check. Please respond with 'OK'.",
            max_tokens=10,
            temperature=0.0,
        )

        for provider_name, client in self.clients.items():
            try:
                if self._is_circuit_breaker_open(provider_name):
                    health_status["providers"][provider_name] = {
                        "status": "circuit_breaker_open",
                        "healthy": False,
                    }
                    continue

                start_time = time.time()
                response = await client.generate_response(test_request)
                response_time = time.time() - start_time

                health_status["providers"][provider_name] = {
                    "status": "healthy",
                    "healthy": True,
                    "response_time": response_time,
                    "model": response.model,
                }

            except Exception as e:
                health_status["providers"][provider_name] = {
                    "status": "unhealthy",
                    "healthy": False,
                    "error": str(e),
                }
                health_status["status"] = "degraded"

        # Overall status
        if not any(
            p.get("healthy", False) for p in health_status["providers"].values()
        ):
            health_status["status"] = "unhealthy"

        return health_status


# Global instance
llm_service = LLMService()
