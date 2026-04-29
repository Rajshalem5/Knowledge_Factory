from fastapi import Depends, HTTPException
from app.core.dependencies import get_current_user


def require_roles(*roles):
    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        return current_user

    return checker