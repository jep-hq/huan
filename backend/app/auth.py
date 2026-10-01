from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app import models, schemas
import httpx


security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> schemas.TokenData:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        authentik_id: str = payload.get("authentik_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return schemas.TokenData(user_id=user_id, authentik_id=authentik_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    token_data = verify_token(token)
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def verify_zitadel_token(access_token: str) -> dict:
    """Verify token with Zitadel and get user info"""
    async with httpx.AsyncClient() as client:
        try:
            # Get user info from Zitadel
            response = await client.get(
                f"{settings.zitadel_url}/oidc/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate Zitadel token: {str(e)}",
            )


def get_or_create_user(db: Session, zitadel_user: dict) -> models.User:
    """Get or create user from Zitadel user info"""
    # Zitadel uses 'sub' for user ID
    zitadel_id = zitadel_user.get("sub")
    email = zitadel_user.get("email")
    # Zitadel uses 'preferred_username' or 'name' for username
    username = zitadel_user.get("preferred_username") or zitadel_user.get("name") or email.split("@")[0]

    if not zitadel_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data from Zitadel"
        )

    # Check if user exists (using authentik_id field for now, can be renamed later)
    user = db.query(models.User).filter(models.User.authentik_id == zitadel_id).first()

    if not user:
        # Create new user
        user = models.User(
            authentik_id=zitadel_id,  # Reusing this field for Zitadel ID
            email=email,
            username=username
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
