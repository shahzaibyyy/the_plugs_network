"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.core.dependencies import DatabaseHealth, RedisHealth

router = APIRouter()


@router.get("/")
async def health_check(
    db_health: DatabaseHealth = Depends(),
    redis_health: RedisHealth = Depends()
) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    Returns:
        Dict containing health status of all services
    """
    return {
        "status": "healthy" if db_health and redis_health else "degraded",
        "services": {
            "database": "healthy" if db_health else "unhealthy",
            "redis": "healthy" if redis_health else "unhealthy",
        }
    }


@router.get("/database")
async def database_health(db_health: DatabaseHealth = Depends()) -> Dict[str, str]:
    """Database-specific health check."""
    return {
        "service": "database",
        "status": "healthy" if db_health else "unhealthy"
    }


@router.get("/redis")
async def redis_health(redis_health: RedisHealth = Depends()) -> Dict[str, str]:
    """Redis-specific health check."""
    return {
        "service": "redis", 
        "status": "healthy" if redis_health else "unhealthy"
    }
