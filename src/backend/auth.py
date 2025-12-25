from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .db import get_db
from .models import User

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing - initialize bcrypt context
_use_bcrypt = True
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # Try to hash a test password to verify bcrypt works
    test_hash = pwd_context.hash("test")
    pwd_context.verify("test", test_hash)
except Exception:
    # Fallback to SHA256 if bcrypt has issues
    _use_bcrypt = False
    import hashlib
    pwd_context = None
    
    def _fallback_hash(password: str) -> str:
        return "sha256$" + hashlib.sha256(password.encode()).hexdigest()
    
    def _fallback_verify(plain: str, hashed: str) -> bool:
        if not hashed.startswith("sha256$"):
            return False
        expected = hashlib.sha256(plain.encode()).hexdigest()
        return hashed[7:] == expected

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    if not _use_bcrypt or pwd_context is None:
        return _fallback_verify(plain_password, hashed_password)
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return _fallback_verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if not _use_bcrypt or pwd_context is None:
        return _fallback_hash(password)
    try:
        return pwd_context.hash(password)
    except Exception:
        return _fallback_hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user

