"""
Custom exceptions for the application.
"""
from fastapi import HTTPException, status


class TwinSecException(Exception):
    """Base exception for TwinSec Studio."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(TwinSecException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(TwinSecException):
    """Raised when user lacks required permissions."""
    pass


class ValidationError(TwinSecException):
    """Raised when data validation fails."""
    pass


class ModelNotFoundError(TwinSecException):
    """Raised when a model is not found."""
    pass


class SimulationError(TwinSecException):
    """Raised when simulation execution fails."""
    pass


class LLMError(TwinSecException):
    """Raised when LLM service fails."""
    pass


# HTTP Exception helpers
def credentials_exception():
    """HTTP 401 Unauthorized exception."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def not_found_exception(resource: str = "Resource"):
    """HTTP 404 Not Found exception."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found"
    )


def forbidden_exception():
    """HTTP 403 Forbidden exception."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )


def conflict_exception(message: str = "Resource already exists"):
    """HTTP 409 Conflict exception."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message
    )


def validation_exception(message: str):
    """HTTP 422 Unprocessable Entity exception."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=message
    )


def internal_server_exception(message: str = "Internal server error"):
    """HTTP 500 Internal Server Error exception."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )
