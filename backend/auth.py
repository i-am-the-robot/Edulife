"""
Authentication and authorization utilities
Handles password hashing, JWT tokens, and role-based access control
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
from dotenv import load_dotenv

from .database import get_db_session
from .models import Admin, User, UserRole

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "edulife-v2-super-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "90"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

# ============================================================================
# JWT TOKEN UTILITIES
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_current_user_or_admin(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session)
) -> Union[User, Admin]:
    """Get current authenticated user (Teacher) or Admin"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        user_type: str = payload.get("type", "teacher")
        
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Check if admin
    if user_type == "admin":
        statement = select(Admin).where(Admin.email == email)
        admin = session.exec(statement).first()
        if admin is None:
            raise credentials_exception
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")
        return admin
    
    # Check if teacher/user
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return user

async def get_current_admin(
    current_user: Union[User, Admin] = Depends(get_current_user_or_admin)
) -> Admin:
    """Ensure current user is an Admin"""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_current_teacher(
    current_user: Union[User, Admin] = Depends(get_current_user_or_admin)
) -> User:
    """Ensure current user is a Teacher"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return current_user

async def get_current_head_teacher(
    current_teacher: User = Depends(get_current_teacher)
) -> User:
    """Ensure current user is a Head Teacher"""
    if current_teacher.role != UserRole.HEAD_TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Head Teacher access required"
        )
    return current_teacher
