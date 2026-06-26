from __future__ import annotations


"""
Auth dependency: supports both JWT Bearer and X-API-Key.
Plug into any route with:  Depends(get_current_user)
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Security, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from utils.config import get_settings
from app.auth.models import CurrentUser

settings = get_settings()

# Config from env
SECRET_KEY  = settings.JWT_SECRET_KEY
ALGORITHM   = settings.JWT_ALGORITHM
EXPIRE_MINS = settings.JWT_EXPIRE_MINUTES
VALID_API_KEYS: set[str] = settings.VALID_API_KEYS

pwd_context    = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme  = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class AuthError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, detail: str = "Authentication failed"):
        self.detail = detail

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def create_access_token(user_id: str) -> tuple[str, int]:
        expire  = datetime.utcnow() + timedelta(minutes=EXPIRE_MINS)
        payload = {"sub": user_id, "exp": expire}
        token   = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token, EXPIRE_MINS * 60


    @staticmethod
    async def get_current_user(
        request:  Request,
        bearer:   Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
        api_key:  Optional[str]                          = Security(api_key_header),
    ) -> CurrentUser:
        # 1. API Key auth (lightweight)
        if api_key and api_key in VALID_API_KEYS:
            user = CurrentUser(user_id=f"api:{api_key[:8]}", auth_type="api_key")
            request.state.user_id = user.user_id
            return user

        # 2. JWT Bearer auth
        if bearer:
            try:
                payload = jwt.decode(bearer.credentials, SECRET_KEY, algorithms=[ALGORITHM])
                user_id: str = payload.get("sub", "")
                if user_id:
                    user = CurrentUser(user_id=user_id, auth_type="jwt")
                    request.state.user_id = user_id
                    return user
            except JWTError:
                pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid credentials. Use Bearer <token> or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )