"""Shared FastAPI dependencies - simplified without multi-tenancy."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.core.security import decode_token
from app.core.enums import Role

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | Candidate:
    """Get current authenticated user or candidate from JWT token."""
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    sub = payload.get("sub")

    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Check candidates first
    stmt = select(Candidate).where(Candidate.id == sub)
    result = await db.execute(stmt)
    candidate = result.scalar_one_or_none()

    if candidate:
        return candidate

    # Check users
    stmt = select(User).where(User.id == sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_role(allowed_roles: list[str]):
    """Decorator to require specific roles for endpoint access."""
    async def role_checker(current_user: User | Candidate = Depends(get_current_user)):
        role = "CANDIDATE" if isinstance(current_user, Candidate) else current_user.role
        
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker
