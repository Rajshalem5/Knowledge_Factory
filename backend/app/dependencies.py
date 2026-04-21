"""
Shared FastAPI dependencies.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.core.security import settings
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.auth.schemas import TokenPayload

security = HTTPBearer()
settings = get_settings()

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User | Candidate:
    """
    Resolve the authenticated user or candidate from the JWT.
    """
    try:
        # Use fallback for dev if no key provided
        algorithm = "RS256" if settings.JWT_PUBLIC_KEY else "HS256"
        secret = settings.JWT_PUBLIC_KEY if settings.JWT_PUBLIC_KEY else "development-secret-key"
        
        payload = jwt.decode(
            token.credentials, secret, algorithms=[algorithm]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    if token_data.role == "CANDIDATE":
        stmt = select(Candidate).where(Candidate.id == token_data.sub)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    else:
        stmt = select(User).where(User.id == token_data.sub)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


def require_role(allowed_roles: list[str]):
    """
    Parameterized dependency to enforce RBAC.
    """
    async def role_checker(current_user: User | Candidate = Depends(get_current_user)):
        role = "CANDIDATE" if isinstance(current_user, Candidate) else current_user.role
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have enough privileges",
            )
        return current_user
    
    return role_checker
