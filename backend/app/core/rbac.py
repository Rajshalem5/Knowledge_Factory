from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user

def require_roles(*allowed_roles):
    def checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return checker