"""
Initialize default admin user.

Creates an admin user with email "admin" and password "admin" if it doesn't exist.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User
from .auth import get_password_hash


def init_admin_user(db: Session) -> User | None:
    """
    Initialize admin user if it doesn't exist.
    
    Args:
        db: Database session.
        
    Returns:
        The admin user if created, None if it already exists.
    """
    admin_email = "admin"
    admin_password = "admin"
    
    # Check if admin user already exists
    existing_admin = db.scalar(select(User).where(User.email == admin_email))
    if existing_admin:
        return None
    
    # Create admin user
    password_hash = get_password_hash(admin_password)
    admin_user = User(
        email=admin_email,
        password_hash=password_hash,
        user_level=1000  # High limit for admin
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return admin_user

