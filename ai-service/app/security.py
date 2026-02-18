"""
Security utilities for input sanitization and JWT authentication.
"""
import re
import html
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise credentials_exception


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    Get the current user from the JWT token.
    
    Args:
        credentials: JWT token credentials from Authorization header
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = verify_token(token)
    return payload


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Optional maximum length limit
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    sanitized = text.strip()
    
    sanitized = html.escape(sanitized)
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_css_selector(selector: str) -> str:
    """
    Sanitize CSS selector to prevent injection.
    
    Args:
        selector: CSS selector to sanitize
        
    Returns:
        Sanitized selector
    """
    if not selector:
        return ""
    
    dangerous_patterns = [
        r'javascript:',
        r'on\w+\s*=',
        r'<script',
        r'</script>',
    ]
    
    for pattern in dangerous_patterns:
        selector = re.sub(pattern, '', selector, flags=re.IGNORECASE)
    
    return selector.strip()


def sanitize_url(url: str) -> str:
    """
    Validate and sanitize URL for scraping.
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL
        
    Raises:
        ValueError: If URL is invalid or potentially dangerous
    """
    url = url.strip().lower()
    
    if not url.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")
    
    dangerous_schemes = ['javascript:', 'data:', 'file:']
    if any(url.startswith(scheme) for scheme in dangerous_schemes):
        raise ValueError("Potentially dangerous URL scheme")
    
    return url
