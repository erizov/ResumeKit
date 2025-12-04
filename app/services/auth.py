"""
Authentication and authorization services.

Provides JWT token generation/verification and password hashing.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import AUTH_SECRET_KEY, AUTH_TOKEN_EXPIRE_MINUTES

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token (typically user ID or email).
            The "sub" field must be convertible to string (JWT spec requirement).
        expires_delta: Optional expiration time delta. If not provided,
            uses AUTH_TOKEN_EXPIRE_MINUTES from config.

    Returns:
        The encoded JWT token string.

    Raises:
        ValueError: If AUTH_SECRET_KEY is not configured.
    """
    if not AUTH_SECRET_KEY:
        raise ValueError("AUTH_SECRET_KEY must be set in environment variables")

    to_encode = data.copy()
    # Ensure "sub" is a string (JWT spec requirement)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=AUTH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT access token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload.

    Raises:
        ValueError: If AUTH_SECRET_KEY is not configured.
        JWTError: If token is invalid, expired, or cannot be decoded.
    """
    if not AUTH_SECRET_KEY:
        raise ValueError("AUTH_SECRET_KEY must be set in environment variables")

    payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[ALGORITHM])
    return payload

