"""
Error handling middleware and utilities.

Provides user-friendly error messages, retry mechanisms, and offline detection.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class UserFriendlyError(Exception):
    """
    Base exception for user-friendly error messages.
    """

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors with user-friendly messages.
    """
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")

    user_message = (
        "Please check your input. " + "; ".join(error_messages)
        if error_messages
        else "Invalid input provided."
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": user_message, "errors": errors},
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors with user-friendly messages.
    """
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": (
                "A database error occurred. Please try again later. "
                "If the problem persists, contact support."
            )
        },
    )


async def user_friendly_exception_handler(
    request: Request, exc: UserFriendlyError
) -> JSONResponse:
    """
    Handle user-friendly errors.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions with user-friendly messages.
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": (
                "An unexpected error occurred. Please try again later. "
                "If the problem persists, contact support."
            )
        },
    )

