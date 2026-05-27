"""
JWT Authentication middleware for WebSocket connections.
"""

import logging
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from app.core.config import get_config

logger = logging.getLogger(__name__)

def verify_proctoring_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify the proctoring JWT token.
    Returns the payload if valid, otherwise None.
    """
    config = get_config()
    logger.info(f"DEBUG: Verifying token with secret prefix: {config.PROCTORING_JWT_SECRET[:5]}...")
    try:
        payload = jwt.decode(
            token,
            config.PROCTORING_JWT_SECRET,
            algorithms=["HS256"]
        )
        
        logger.info(f"JWT decoded successfully. Payload subject: {payload.get('sub')}")

        # Validate type
        token_type = payload.get("type")
        if token_type != "proctoring_ws":
            logger.warning(f"Invalid token type: {token_type}")
            return None
            
        session_id = payload.get("session_id")
        logger.info(f"Proctoring token verified for session: {session_id}, user: {payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Proctoring token has expired")
        return None
    except JWTError as e:
        logger.warning(f"JWT Verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify the main backend access token.
    Signed with JWT_SECRET_KEY.
    """
    config = get_config()
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except Exception as e:
        logger.warning(f"Access token verification failed: {e}")
        return None


from fastapi import Request, HTTPException

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to protect HTTP endpoints.
    Expects Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    logger.info(f"Access token verified for user: {payload.get('sub')}")
    return payload
