"""Shared FastAPI dependencies."""

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

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | Candidate:
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    sub = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")

    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if role == "CANDIDATE":
        stmt = select(Candidate).where(Candidate.id == sub)
    else:
        stmt = select(User).where(User.id == sub)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Attach tenant_id from JWT to the user object for downstream access
    user._jwt_tenant_id = tenant_id  # type: ignore[attr-defined]

    return user


def require_role(allowed_roles: list[str]):
    async def role_checker(current_user: User | Candidate = Depends(get_current_user)):
        role = "CANDIDATE" if isinstance(current_user, Candidate) else current_user.role
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_checker
