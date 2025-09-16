"""
Logging configuration with structured logging support.
"""
import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from contextvars import ContextVar

from .settings import settings

# Context variable for request correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        if correlation_id.get():
            log_data["correlation_id"] = correlation_id.get()
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None,
            }
        
        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Custom formatter for human-readable text logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        correlation = f" [{correlation_id.get()}]" if correlation_id.get() else ""
        
        base_format = f"{timestamp} | {record.levelname:8} | {record.name:20} | {record.getMessage()}{correlation}"
        
        if record.exc_info:
            base_format += f"\n{self.formatException(record.exc_info)}"
        
        return base_format


def setup_logging() -> None:
    """Setup application logging configuration."""
    
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Choose formatter based on settings
    if settings.log_format.lower() == "json":
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter()
    
    # Setup handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)
    
    # File handler if specified
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Configure specific loggers
    configure_loggers(log_level)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": settings.log_level,
            "log_format": settings.log_format,
            "log_file": settings.log_file,
            "environment": settings.environment.value,
        }
    )


def configure_loggers(log_level: int) -> None:
    """Configure specific loggers with appropriate levels."""
    
    # Application loggers
    logging.getLogger("app").setLevel(log_level)
    
    # Third-party library loggers
    if settings.is_production:
        # Reduce noise in production
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    else:
        # More verbose in development
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        if settings.database_echo:
            logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        else:
            logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Celery loggers
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("celery.task").setLevel(logging.INFO)
    
    # Redis loggers
    logging.getLogger("redis").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name, typically __name__
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(request_id: Optional[str] = None) -> str:
    """
    Set correlation ID for request tracking.
    
    Args:
        request_id: Optional request ID, generates UUID if not provided
        
    Returns:
        str: The correlation ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    correlation_id.set(request_id)
    return request_id


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID.
    
    Returns:
        Optional[str]: Current correlation ID or None
    """
    return correlation_id.get()


def log_request(method: str, url: str, status_code: int, duration: float, **kwargs) -> None:
    """
    Log HTTP request with structured data.
    
    Args:
        method: HTTP method
        url: Request URL
        status_code: HTTP status code
        duration: Request duration in seconds
        **kwargs: Additional fields to log
    """
    logger = get_logger("app.requests")
    
    log_data = {
        "http_method": method,
        "url": url,
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2),
        **kwargs
    }
    
    if status_code >= 400:
        logger.error("HTTP request failed", extra=log_data)
    else:
        logger.info("HTTP request completed", extra=log_data)


def log_database_query(query: str, duration: float, **kwargs) -> None:
    """
    Log database query with performance metrics.
    
    Args:
        query: SQL query
        duration: Query duration in seconds
        **kwargs: Additional fields to log
    """
    logger = get_logger("app.database")
    
    log_data = {
        "query": query[:500] + "..." if len(query) > 500 else query,  # Truncate long queries
        "duration_ms": round(duration * 1000, 2),
        **kwargs
    }
    
    if duration > 1.0:  # Log slow queries as warnings
        logger.warning("Slow database query", extra=log_data)
    else:
        logger.debug("Database query executed", extra=log_data)


# Initialize logging on module import
if not settings.is_testing:  # Skip auto-setup during testing
    setup_logging()