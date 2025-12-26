from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
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

# OAuth2 scheme - auto_error=False allows us to handle errors manually
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# HTTPBearer for more reliable token extraction
http_bearer = HTTPBearer(auto_error=False)


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
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user from JWT token."""
    import logging
    logger = logging.getLogger(__name__)
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        logger.info("get_current_user: No credentials provided")
        raise credentials_exception
    
    token = credentials.credentials
    logger.info(f"get_current_user: Token received (length: {len(token)}, first 20 chars: {token[:20]}...)")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            logger.warning("get_current_user: No 'sub' in token payload")
            raise credentials_exception
        # Convert string back to int (JWT sub must be string)
        try:
            user_id: int = int(user_id_str)
        except (ValueError, TypeError):
            logger.error(f"get_current_user: Invalid user_id format: {user_id_str}")
            raise credentials_exception
        logger.info(f"get_current_user: Token decoded successfully, user_id: {user_id}")
    except JWTError as e:
        logger.error(f"get_current_user: JWT decode error: {type(e).__name__}: {e}")
        # SECURITY: Don't log SECRET_KEY even partially - it's a security risk
        logger.error(f"get_current_user: Token validation failed (SECRET_KEY length: {len(SECRET_KEY)})")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"get_current_user: User with ID {user_id} not found in database")
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    logger.debug(f"get_current_user: Successfully authenticated user {user.email}")
    return user

