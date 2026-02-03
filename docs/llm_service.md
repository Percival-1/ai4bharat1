# LLM Service Documentation

## Overview

The LLM Service provides a unified interface for interacting with multiple Large Language Model providers (OpenAI, Anthropic) with comprehensive error handling, retry mechanisms, and monitoring capabilities.

## Features

- **Multi-provider support**: OpenAI and Anthropic APIs
- **Automatic failover**: Seamless switching between providers when one fails
- **Retry mechanisms**: Exponential backoff for transient failures
- **Circuit breaker pattern**: Prevents cascade failures
- **Request/response logging**: Comprehensive monitoring and debugging
- **API key rotation support**: Easy configuration management
- **Health checks**: Monitor provider availability
- **Metrics collection**: Track usage, performance, and errors

## Configuration

### Environment Variables

```bash
# Primary and fallback providers
PRIMARY_LLM_PROVIDER=openai
FALLBACK_LLM_PROVIDER=anthropic

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# LLM Configuration
LLM_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0
```

### Model Mapping

The service automatically maps between provider-specific models:

- `gpt-3.5-turbo` → `claude-3-haiku-20240307`
- `gpt-4` → `claude-3-sonnet-20240229`
- `gpt-4-turbo` → `claude-3-opus-20240229`

## Usage

### Basic Usage

```python
from app.services.llm_service import llm_service

# Generate response
response = await llm_service.generate_response(
    prompt="What is the weather like today?",
    system_message="You are a helpful agricultural assistant.",
    max_tokens=100,
    temperature=0.7
)

print(response.content)
print(f"Provider: {response.provider}")
print(f"Tokens used: {response.tokens_used}")
```

### API Endpoints

#### Generate Response
```http
POST /api/v1/llm/generate
Content-Type: application/json

{
    "prompt": "What is the weather like today?",
    "system_message": "You are a helpful assistant.",
    "max_tokens": 100,
    "temperature": 0.7,
    "model": "gpt-3.5-turbo",
    "provider": "openai",
    "metadata": {"user_id": "123"}
}
```

#### Get Metrics
```http
GET /api/v1/llm/metrics
```

Response:
```json
{
    "total_requests": 100,
    "successful_requests": 95,
    "failed_requests": 5,
    "success_rate": 0.95,
    "total_tokens_used": 5000,
    "average_response_time": 1.5,
    "provider_usage": {"openai": 60, "anthropic": 35},
    "error_counts": {"LLMTimeoutError": 3},
    "circuit_breaker_state": {
        "openai": {"failures": 0, "state": "closed"},
        "anthropic": {"failures": 1, "state": "closed"}
    },
    "available_providers": ["openai", "anthropic"]
}
```

#### Health Check
```http
GET /api/v1/llm/health
```

#### Get Available Providers
```http
GET /api/v1/llm/providers
```

#### Reset Metrics
```http
POST /api/v1/llm/metrics/reset
```

## Error Handling

The service implements comprehensive error handling:

### Error Types

- **LLMError**: Base exception for all LLM service errors
- **LLMProviderError**: Provider-specific errors
- **LLMTimeoutError**: Request timeout errors
- **LLMRateLimitError**: Rate limit exceeded errors

### Circuit Breaker

The circuit breaker pattern prevents cascade failures:

- **Closed**: Normal operation
- **Open**: Provider is failing, requests are blocked
- **Half-open**: Testing if provider has recovered

Circuit breaker opens after 3 consecutive failures and transitions to half-open after 5 minutes.

### Retry Logic

- Maximum retries: 3 (configurable)
- Exponential backoff: 1s, 2s, 4s
- Retries on: Timeout and rate limit errors
- No retry on: Provider errors

## Monitoring

### Metrics

The service tracks comprehensive metrics:

- Request counts (total, successful, failed)
- Success rate
- Token usage
- Response times
- Provider usage distribution
- Error counts by type
- Circuit breaker states

### Logging

All requests and responses are logged with:

- Request details (prompt, parameters)
- Response metadata (provider, model, tokens)
- Error information
- Performance metrics

## Best Practices

1. **API Key Management**: Store API keys securely and rotate regularly
2. **Rate Limiting**: Monitor usage to avoid rate limits
3. **Error Handling**: Always handle LLM errors gracefully
4. **Monitoring**: Set up alerts for high error rates
5. **Fallback**: Configure multiple providers for redundancy
6. **Caching**: Consider caching responses for repeated queries

## Troubleshooting

### Common Issues

1. **No providers available**: Check API key configuration
2. **High error rates**: Check provider status and rate limits
3. **Slow responses**: Monitor response times and adjust timeouts
4. **Circuit breaker open**: Check provider health and error logs

### Debug Mode

Enable debug logging to see detailed request/response information:

```bash
LOG_LEVEL=DEBUG
```

## Security Considerations

- API keys are never logged or exposed
- All requests are validated and sanitized
- Rate limiting prevents abuse
- Circuit breakers prevent resource exhaustion
- Comprehensive error handling prevents information leakage