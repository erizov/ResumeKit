"""
Authentication and authorization services.

Provides JWT token generation/verification and password hashing.
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import AUTH_SECRET_KEY, AUTH_TOKEN_EXPIRE_HOURS


def _get_auth_secret_key() -> str | None:
    """
    Get AUTH_SECRET_KEY, ensuring .env is loaded.
    
    This function uses the same logic as the routes module to ensure
    consistency between validation and token operations.
    """
    # Try to read directly from .env file first
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        # Read .env file directly
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == 'AUTH_SECRET_KEY' and value:
                        return value
        
        # If not found in file, try load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
        key = os.getenv("AUTH_SECRET_KEY")
        if key:
            return key
    
    # Fallback to config module value
    if AUTH_SECRET_KEY:
        return AUTH_SECRET_KEY
    
    return None

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
    # Use the same key source as validation to ensure consistency
    secret_key = _get_auth_secret_key()
    if not secret_key:
        raise ValueError("AUTH_SECRET_KEY must be set in environment variables")

    to_encode = data.copy()
    # Ensure "sub" is a string (JWT spec requirement)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(hours=AUTH_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
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
    # Use the same key source as validation to ensure consistency
    secret_key = _get_auth_secret_key()
    if not secret_key:
        raise ValueError("AUTH_SECRET_KEY must be set in environment variables")

    payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    return payload

