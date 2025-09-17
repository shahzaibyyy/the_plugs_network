"""
FastAPI dependency injection for database and other services.
"""
from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import Engine
import redis

from app.config.database import db_config
from app.config.redis import redis_config, get_cache_manager, get_session_manager
from app.config.security import security_config


def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session with proper lifecycle management.
    
    This dependency provides a database session that automatically:
    - Commits transactions on success
    - Rolls back transactions on error
    - Closes the session when done
    
    Yields:
        Session: SQLAlchemy database session
    """
    session = db_config.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_database_engine() -> Engine:
    """
    FastAPI dependency for database engine.
    
    Returns:
        Engine: SQLAlchemy database engine
    """
    return db_config.engine


def get_database_health() -> bool:
    """
    FastAPI dependency for database health check.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    return db_config.health_check()


def get_redis_client() -> redis.Redis:
    """
    FastAPI dependency for Redis client.
    
    Returns:
        redis.Redis: Redis client instance
    """
    return redis_config.client


def get_cache_manager_dependency():
    """
    FastAPI dependency for cache manager.
    
    Returns:
        CacheManager: Cache manager instance
    """
    return get_cache_manager()


def get_session_manager_dependency():
    """
    FastAPI dependency for session manager.
    
    Returns:
        SessionManager: Session manager instance
    """
    return get_session_manager()


def get_redis_health() -> bool:
    """
    FastAPI dependency for Redis health check.
    
    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    return redis_config.health_check()


# Security dependencies
security_scheme = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """
    FastAPI dependency for optional user authentication.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Optional user data if token is valid, None otherwise
    """
    if not credentials:
        return None
    
    try:
        payload = security_config.verify_token(credentials.credentials)
        return payload
    except HTTPException:
        return None


def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """
    FastAPI dependency for required user authentication.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User data if token is valid
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = security_config.verify_token(credentials.credentials)
    return payload


def get_current_active_user(
    current_user: dict = Depends(get_current_user_required)
):
    """
    FastAPI dependency for active user authentication.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User data if user is active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(
    current_user: dict = Depends(get_current_active_user)
):
    """
    FastAPI dependency for admin user authentication.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User data if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Type aliases for dependency injection
DatabaseSession = Annotated[Session, Depends(get_database_session)]
DatabaseEngine = Annotated[Engine, Depends(get_database_engine)]
DatabaseHealth = Annotated[bool, Depends(get_database_health)]
RedisClient = Annotated[redis.Redis, Depends(get_redis_client)]
RedisHealth = Annotated[bool, Depends(get_redis_health)]
CacheManager = Annotated[object, Depends(get_cache_manager_dependency)]
SessionManager = Annotated[object, Depends(get_session_manager_dependency)]
CurrentUser = Annotated[dict, Depends(get_current_user_required)]
CurrentActiveUser = Annotated[dict, Depends(get_current_active_user)]
CurrentAdminUser = Annotated[dict, Depends(get_current_admin_user)]
OptionalUser = Annotated[dict, Depends(get_current_user_optional)]