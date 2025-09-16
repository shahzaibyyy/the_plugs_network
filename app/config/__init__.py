"""
Configuration module for The Plugs API.

This module provides centralized configuration management with environment-based
settings, database configuration, logging, and security settings.
"""

from .settings import settings, Environment
from .database import db_config, get_database_session, get_database_engine, Base
from .logging import (
    setup_logging,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    log_request,
    log_database_query,
)
from .security import (
    security_config,
    cors_config,
    rate_limit_config,
    security_scheme,
    pwd_context,
)

__all__ = [
    # Settings
    "settings",
    "Environment",
    
    # Database
    "db_config",
    "get_database_session",
    "get_database_engine",
    "Base",
    
    # Logging
    "setup_logging",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "log_request",
    "log_database_query",
    
    # Security
    "security_config",
    "cors_config",
    "rate_limit_config",
    "security_scheme",
    "pwd_context",
]