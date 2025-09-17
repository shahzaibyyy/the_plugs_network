"""
API v1 router that includes all v1 endpoints.
"""
from fastapi import APIRouter

from . import (
    auth,
    health,
    users,
    organizations,
    # events,
    # networking,
    # expenses,
    # media,
    # analytics,
    # notifications,
    # admin,
    # tenants
)

# Create v1 router
router = APIRouter()

# Include endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])

# Uncomment these as you implement the corresponding modules
# router.include_router(events.router, prefix="/events", tags=["Events"])
# router.include_router(networking.router, prefix="/networking", tags=["Networking"])
# router.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
# router.include_router(media.router, prefix="/media", tags=["Media"])
# router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
# router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
# router.include_router(admin.router, prefix="/admin", tags=["Admin"])
# router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
