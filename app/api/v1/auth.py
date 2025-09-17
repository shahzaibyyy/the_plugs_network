"""
Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from app.core.dependencies import DatabaseSession

router = APIRouter()


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DatabaseSession = Depends()
):
    """User login endpoint."""
    # TODO: Implement authentication logic
    return {
        "message": "Authentication endpoint - to be implemented",
        "username": form_data.username
    }


@router.post("/register")
async def register(db: DatabaseSession = Depends()):
    """User registration endpoint."""
    # TODO: Implement user registration
    return {"message": "Registration endpoint - to be implemented"}


@router.post("/refresh")
async def refresh_token():
    """Refresh JWT token endpoint."""
    # TODO: Implement token refresh
    return {"message": "Token refresh endpoint - to be implemented"}


@router.post("/logout")
async def logout():
    """User logout endpoint."""
    # TODO: Implement logout logic
    return {"message": "Logout endpoint - to be implemented"}
