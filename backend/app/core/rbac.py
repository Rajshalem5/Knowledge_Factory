# app/core/rbac.py
# Legacy RBAC decorator — kept for backward compatibility.
# Prefer app.dependencies.require_role for new code.

from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user
from app.core.enums import Role


def require_roles(*allowed_roles):
    def checker(
        current_user=Depends(get_current_user)
    ):
        raw_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        role = Role.normalize(raw_role)

        normalized_allowed = [Role.normalize(r) for r in allowed_roles]

        if role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return current_user

    return checker
