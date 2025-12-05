"""
Authentication endpoints.

Provides signup, login, and logout functionality using JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import AUTH_SECRET_KEY
import os
from pathlib import Path
from dotenv import load_dotenv

def _get_auth_secret_key():
    """Get AUTH_SECRET_KEY, ensuring .env is loaded."""
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
                        print(f"[Auth] _get_auth_secret_key: Found key in .env file (length: {len(value)})")
                        return value
        
        # If not found in file, try load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
        key = os.getenv("AUTH_SECRET_KEY")
        if key:
            print(f"[Auth] _get_auth_secret_key: Found key via load_dotenv (length: {len(key)})")
            return key
    
    # Fallback to config module value
    if AUTH_SECRET_KEY:
        print(f"[Auth] _get_auth_secret_key: Using config module value (length: {len(AUTH_SECRET_KEY)})")
        return AUTH_SECRET_KEY
    
    print("[Auth] _get_auth_secret_key: WARNING - No AUTH_SECRET_KEY found!")
    return None
from ..db import get_db
from ..models import User
from ..schemas import Token, UserLogin, UserResponse, UserSignup
from ..services.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials.
        db: Database session.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    # Authentication check
    auth_key = _get_auth_secret_key()
    if not auth_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )
    
    # Extract and verify JWT token
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        user_id = int(user_id_str)
    except (ValueError, JWTError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token parsing failed: {str(e)}",
        ) from e

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)) -> UserResponse:
    """
    Create a new user account.

    Args:
        user_data: User signup data (email and password).
        db: Database session.

    Returns:
        The created user information.

    Raises:
        HTTPException: If email already exists or signup fails.
    """
    # Check if user already exists
    existing_user = db.scalar(select(User).where(User.email == user_data.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    password_hash = get_password_hash(user_data.password)
    user = User(email=user_data.email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id, 
        email=user.email, 
        user_level=user.user_level,
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    """
    Authenticate user and return JWT token.

    Args:
        credentials: User login credentials (email and password).
        db: Database session.

    Returns:
        JWT access token.

    Raises:
        HTTPException: If credentials are invalid.
    """
    print(f"[Auth] Login attempt for: {credentials.email}")
    
    # Authentication check
    auth_key = _get_auth_secret_key()
    if not auth_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Please set AUTH_SECRET_KEY.",
        )

    # Find user by email
    user = db.scalar(select(User).where(User.email == credentials.email))
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user (from dependency).

    Returns:
        User information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        user_level=current_user.user_level,
        created_at=current_user.created_at,
    )


@router.post("/logout")
def logout() -> dict[str, str]:
    """
    Logout endpoint (client-side token removal).

    Since JWT tokens are stateless, logout is handled client-side
    by removing the token. This endpoint exists for API consistency.

    Returns:
        Success message.
    """
    return {"message": "Successfully logged out"}

