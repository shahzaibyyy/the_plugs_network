"""
Main API router that includes all API version routers.
"""
from fastapi import APIRouter

from app.api.v1 import router as v1_router

# Create main API router
api_router = APIRouter()

# Include versioned API routers
api_router.include_router(v1_router, prefix="/v1", tags=["v1"])

# Health check can be accessed directly
@api_router.get("/health")
async def api_health():
    """API health check endpoint."""
    return {"status": "healthy", "version": "v1"}
