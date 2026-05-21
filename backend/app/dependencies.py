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

    # Normalize role to canonical form (handles SUPERADMIN→SUPER_ADMIN etc.)
    normalized_role = Role.normalize(user.role.value if hasattr(user.role, 'value') else str(user.role))
    if normalized_role != user.role:
        import logging
        logging.getLogger(__name__).warning(
            "[get_current_user] Role normalized: %s → %s for user %s",
            user.role, normalized_role, user.email,
        )
        user.role = normalized_role

    return user


def require_role(allowed_roles: list[str]):
    """Decorator to require specific roles for endpoint access.
    Roles are normalized before comparison to handle legacy/dirty formats.
    """
    async def role_checker(current_user: User | Candidate = Depends(get_current_user)):
        if isinstance(current_user, Candidate):
            role = "CANDIDATE"
        else:
            raw = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
            role = Role.normalize(raw)

        normalized_allowed = [Role.normalize(r) for r in allowed_roles]

        if role not in normalized_allowed:
            import logging
            logging.warning(
                "[require_role] Permission denial: User %s with role %s tried to access resource requiring %s",
                current_user.email, role, normalized_allowed,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker
