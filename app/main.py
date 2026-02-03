"""
FastAPI application entry point for the AI-Driven Agri-Civic Intelligence Platform.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.api import health, ivr
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware

settings = get_settings()

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {response.status_code} - "
                f"Time: {process_time:.4f}s - "
                f"Path: {request.url.path}"
            )

            # Add response time header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} - "
                f"Time: {process_time:.4f}s - "
                f"Path: {request.url.path}"
            )
            raise


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring response times."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Check if response time exceeds the configured limit
        if process_time > settings.max_response_time_seconds:
            logger.warning(
                f"Slow response detected: {process_time:.4f}s > {settings.max_response_time_seconds}s - "
                f"Path: {request.url.path}"
            )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting AI-Driven Agri-Civic Intelligence Platform")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # TODO: Initialize database connections
    # TODO: Initialize Redis connections
    # TODO: Initialize external API clients
    # TODO: Load ML models and vector databases

    yield

    # Shutdown
    logger.info("🛑 Shutting down AI-Driven Agri-Civic Intelligence Platform")

    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Cleanup external API clients
    # TODO: Cleanup ML models and vector databases


app = FastAPI(
    title="AI-Driven Agri-Civic Intelligence Platform",
    description="Multilingual agricultural intelligence platform for farmers and rural communities",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)

# Security middleware
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure with actual allowed hosts in production
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ResponseTimeMiddleware)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
                "timestamp": time.time(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)} - Path: {request.url.path}", exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "path": str(request.url.path),
                "timestamp": time.time(),
            }
        },
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(ivr.router, prefix="/api/v1/ivr", tags=["ivr"])

# Import and include vector database router
from app.api import vector_db

app.include_router(vector_db.router, prefix="/api/v1", tags=["vector-db"])

# Import and include RAG router
from app.api import rag

app.include_router(rag.router, prefix="/api/v1", tags=["rag"])

# Import and include LLM router
from app.api import llm

app.include_router(llm.router, prefix="/api/v1", tags=["llm"])

# Import and include Translation router
from app.api import translation

app.include_router(translation.router, prefix="/api/v1", tags=["translation"])


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "AI-Driven Agri-Civic Intelligence Platform",
        "version": "0.1.0",
        "description": "Multilingual agricultural intelligence platform for farmers and rural communities",
        "environment": settings.environment,
        "docs_url": "/docs" if settings.environment != "production" else None,
        "health_check": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower(),
    )
