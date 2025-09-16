"""
Custom exception classes for the application.
"""
from typing import Any, Dict, Optional


class BaseApplicationException(Exception):
    """Base exception class for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseApplicationException):
    """Raised when data validation fails."""
    pass


class NotFoundError(BaseApplicationException):
    """Raised when a requested resource is not found."""
    pass


class DatabaseError(BaseApplicationException):
    """Raised when database operations fail."""
    pass


class TransactionError(DatabaseError):
    """Raised when database transaction operations fail."""
    pass