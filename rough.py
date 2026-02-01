import time
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, status, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.config import get_settings
from app.db.session import get_db

settings = get_settings()
router = APIRouter()

# --- Global Health Cache ---
# Prevents "Health Check Storms" from overwhelming the DB
_health_cache: Dict[str, Any] = {
    "data": None,
    "expiry": 0
}
CACHE_TTL_SECONDS = 30 

async def get_system_health(db: AsyncSession) -> Dict[str, Any]:
    """Coordinates real-time checks with a 30-second throttle."""
    now = time.time()
    
    if _health_cache["data"] and now < _health_cache["expiry"]:
        return _health_cache["data"]

    # 1. Database Connectivity Check
    db_status = await check_database(db)
    
    # 2. Redis Connectivity Check
    redis_status = await check_redis()
    
    # 3. Determine Overall Status
    # Critical services: if DB or Redis is down, the app is "unhealthy"
    is_healthy = db_status["status"] == "healthy" and redis_status["status"] == "healthy"
    
    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status,
        }
    }

    # Update global cache
    _health_cache["data"] = health_data
    _health_cache["expiry"] = now + CACHE_TTL_SECONDS
    
    return health_data

async def check_database(db: AsyncSession) -> Dict[str, str]:
    try:
        # statement_timeout ensures the query doesn't hang the worker thread
        await db.execute(text("SET statement_timeout = '2000'")) 
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}

async def check_redis() -> Dict[str, str]:
    try:
        # socket_connect_timeout prevents long waits if the network path is dead
        r = redis.from_url(
            settings.REDIS_URL, 
            socket_connect_timeout=2.0, 
            socket_timeout=2.0
        )
        await r.ping()
        return {"status": "healthy", "message": "Connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}

# --- Endpoints ---

@router.get("/health/detailed")
async def detailed_health_check(
    response: Response, 
    db: AsyncSession = Depends(get_db)
):
    health_info = await get_system_health(db)
    
    # If any core service is down, return 503. 
    # This tells Load Balancers (AWS, Nginx) to stop sending traffic here.
    if health_info["status"] != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        **health_info,
        "version": "0.1.0",
        "environment": settings.environment,
    }