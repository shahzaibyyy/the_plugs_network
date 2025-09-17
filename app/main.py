"""
The Plugs - Enterprise FastAPI Application
"""
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.config.settings import settings
from app.config.database import db_config
from app.config.redis import redis_config
from app.config.security import cors_config
from app.config.logging import setup_logging, set_correlation_id, get_correlation_id, log_request
from app.core.exceptions import BaseApplicationException
from app.api.router import api_router
from app.utils.helpers import get_client_ip

# Setup logging first
if not settings.is_testing:
    setup_logging()

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Set correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Add correlation ID to response headers
        start_time = time.time()
        client_ip = get_client_ip(dict(request.headers))
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", ""),
                "correlation_id": correlation_id
            }
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = correlation_id
            
            # Log request completion
            log_request(
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration=duration,
                client_ip=client_ip,
                correlation_id=correlation_id
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": client_ip,
                    "error": str(e),
                    "duration": duration,
                    "correlation_id": correlation_id
                },
                exc_info=e
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting The Plugs API application")
    
    try:
        # Test database connection
        if db_config.health_check():
            logger.info("Database connection established")
        else:
            logger.error("Database connection failed")
            raise RuntimeError("Cannot connect to database")
        
        # Test Redis connection
        if redis_config.health_check():
            logger.info("Redis connection established")
        else:
            logger.error("Redis connection failed")
            raise RuntimeError("Cannot connect to Redis")
        
        logger.info("Application startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down The Plugs API application")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="Enterprise B2B Networking and Event Management Platform",
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        **cors_config.get_cors_config()
    )
    
    # Add trusted host middleware for production
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure with actual allowed hosts
        )
    
    # Add custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Configure exception handlers
    configure_exception_handlers(app)
    
    # Add health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        try:
            # Check database
            db_healthy = db_config.health_check()
            
            # Check Redis
            redis_healthy = redis_config.health_check()
            
            # Overall health
            healthy = db_healthy and redis_healthy
            
            health_data = {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": time.time(),
                "version": settings.app_version,
                "environment": settings.environment.value,
                "services": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "redis": "healthy" if redis_healthy else "unhealthy"
                }
            }
            
            status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
            return JSONResponse(content=health_data, status_code=status_code)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "timestamp": time.time(),
                    "error": str(e)
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    # Add metrics endpoint for monitoring
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Basic metrics endpoint."""
        try:
            db_info = db_config.get_connection_info()
            redis_info = redis_config.get_connection_info()
            
            return {
                "database": db_info,
                "redis": redis_info,
                "correlation_id": get_correlation_id()
            }
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return JSONResponse(
                content={"error": "Metrics unavailable"},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
            "docs_url": "/docs" if not settings.is_production else None,
            "health_url": "/health",
            "api_url": "/api"
        }
    
    return app


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers."""
    
    @app.exception_handler(BaseApplicationException)
    async def application_exception_handler(request: Request, exc: BaseApplicationException):
        """Handle custom application exceptions."""
        logger.error(
            f"Application exception: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "url": str(request.url),
                "method": request.method,
                "correlation_id": get_correlation_id()
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "timestamp": time.time(),
                    "correlation_id": get_correlation_id()
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        logger.warning(
            f"Validation error: {str(exc)}",
            extra={
                "errors": exc.errors(),
                "url": str(request.url),
                "method": request.method,
                "correlation_id": get_correlation_id()
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "timestamp": time.time(),
                    "correlation_id": get_correlation_id()
                }
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            f"HTTP exception: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "url": str(request.url),
                "method": request.method,
                "correlation_id": get_correlation_id()
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "timestamp": time.time(),
                    "correlation_id": get_correlation_id()
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        logger.warning(
            f"Starlette HTTP exception: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "url": str(request.url),
                "method": request.method,
                "correlation_id": get_correlation_id()
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "timestamp": time.time(),
                    "correlation_id": get_correlation_id()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(
            f"Unexpected error: {str(exc)}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "correlation_id": get_correlation_id()
            },
            exc_info=exc
        )
        
        # Don't expose internal errors in production
        error_message = "Internal server error" if settings.is_production else str(exc)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": error_message,
                    "timestamp": time.time(),
                    "correlation_id": get_correlation_id()
                }
            }
        )


# Create application instance
app = create_application()

# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
