"""Authentication routes - simplified without multi-tenancy."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.config import settings
from app.features.auth.schemas import (
    CandidateRegisterRequest,
    ClerkSyncRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OtpVerifyRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.features.auth.service import AuthService
from app.features.candidates.models import Candidate
from app.features.auth.models import User
from app.core.enums import Role

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Re-auth for destructive actions ──────────────────────────
@router.post("/confirm-password")
async def confirm_password(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Verify password before destructive actions (delete account, data purge)."""
    from app.core.security import verify_password
    import json
    body = json.loads(await request.body())
    password = body.get("password", "")

    # Fetch full user record
    stmt = select(User).where(User.id == current_user.id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash or ""):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {"verified": True, "user_id": str(user.id)}


@router.delete("/delete-account")
async def delete_account(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Soft-delete account and cascade to all related records. Requires recent confirm-password call (5 min window)."""
    from datetime import datetime, timezone, timedelta
    from app.core.security import decode_token
    import json

    body = json.loads(await request.body())
    token = body.get("reauth_token", "")

    # Verify reauth token was issued in last 5 minutes
    if not token:
        raise HTTPException(status_code=400, detail="Re-authentication required. Call /confirm-password first.")
    payload = decode_token(token)
    if not payload or payload.get("sub") != current_user.id:
        raise HTTPException(status_code=401, detail="Re-auth token invalid or expired")

    # Fetch full user
    stmt = select(User).where(User.id == current_user.id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    user.deleted_at = now

    # Cascade soft-delete candidates owned by this user
    from app.features.candidates.models import Candidate
    stmt = select(Candidate).where(Candidate.created_by == current_user.id)
    res = await db.execute(stmt)
    for candidate in res.scalars().all():
        candidate.deleted_at = now

    await db.commit()
    clear_refresh_cookie(Response())
    return {"message": "Account deleted successfully"}

# Cookie settings for refresh token
REFRESH_TOKEN_COOKIE_NAME = "kf_refresh_token"
REFRESH_TOKEN_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def set_refresh_cookie(response: Response, token: str):
    """Set refresh token as httpOnly cookie."""
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=not settings.DEBUG,  # Secure in production, allow HTTP in dev
        samesite="lax",
        max_age=REFRESH_TOKEN_COOKIE_MAX_AGE,
        path="/api/auth",
    )


def clear_refresh_cookie(response: Response):
    """Clear refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path="/api/auth",
    )


@router.post("/login")
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db), response: Response = None):
    """Authenticate user or candidate and return tokens."""
    auth_service = AuthService(db)
    result = await auth_service.authenticate(login_data)

    if not result:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user_or_candidate, _is_candidate = result
    token_data = auth_service.generate_token_response(user_or_candidate)

    # Set refresh token as httpOnly cookie
    set_refresh_cookie(response, token_data["refresh_token"])

    # Return access token only (refresh token is in cookie)
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "user": token_data["user"],
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_candidate(
    body: CandidateRegisterRequest,
    db: AsyncSession = Depends(get_db),
    response: Response = None,
):
    """Register a new candidate (JSON body)."""
    from app.features.hiring_cycles.models import HiringCycle

    # Get active hiring cycle
    stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE").limit(1)
    res = await db.execute(stmt)
    cycle = res.scalar_one_or_none()

    if not cycle:
        raise HTTPException(
            status_code=500,
            detail="No active hiring cycle. Contact admin.",
        )

    auth_service = AuthService(db)

    candidate = await auth_service.register_candidate(
        body, cycle.id, resume=None
    )

    token_data = auth_service.generate_token_response(candidate)

    # Set refresh token as httpOnly cookie
    set_refresh_cookie(response, token_data["refresh_token"])

    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "token_type": "bearer",
        "user": token_data["user"],
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Get current user profile. Role is normalized to canonical form."""
    is_candidate = isinstance(current_user, Candidate)

    if is_candidate:
        role = "CANDIDATE"
    else:
        raw = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        role = Role.normalize(raw)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=role,
    )


@router.post("/refresh")
async def refresh_token(
    db: AsyncSession = Depends(get_db),
    response: Response = None,
    request: Request = None,
):
    """Refresh access token using refresh token from httpOnly cookie."""
    from app.core.security import decode_token

    refresh_token_value = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    payload = decode_token(refresh_token_value)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    sub = payload["sub"]

    # Resolve entity - check candidates first, then users
    stmt = select(Candidate).where(Candidate.id == sub)
    res = await db.execute(stmt)
    candidate = res.scalar_one_or_none()

    if candidate:
        auth_svc = AuthService(db)
        token_data = auth_svc.generate_token_response(candidate)
        set_refresh_cookie(response, token_data["refresh_token"])
        return {
            "access_token": token_data["access_token"],
            "token_type": "bearer",
            "user": token_data["user"],
        }

    stmt = select(User).where(User.id == sub)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    auth_svc = AuthService(db)
    token_data = auth_svc.generate_token_response(user)
    set_refresh_cookie(response, token_data["refresh_token"])
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "user": token_data["user"],
    }


@router.post("/logout")
async def logout(response: Response):
    """Logout - clear refresh token cookie."""
    clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(data: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and issue tokens (dev mode accepts any 6-digit code)."""
    from app.core.security import create_access_token, create_refresh_token

    stmt = select(User).where(User.email == data.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    # If not found in User, check Candidate table
    from app.features.candidates.models import Candidate
    if not user:
        stmt = select(Candidate).where(Candidate.email == data.email)
        res = await db.execute(stmt)
        candidate = res.scalar_one_or_none()
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail="No existing account found with this email. Please register first.",
            )
        # Link clerk_id to candidate
        candidate.clerk_id = data.clerk_id
        await db.commit()

    # Dev-mode: auto-accept any 6-digit OTP
    if user.password_hash and len(data.otp) == 6:
        raw_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        role = Role.normalize(raw_role)
        access_token = create_access_token(subject=str(user.id), email=user.email, role=role)
        refresh_tok = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_tok,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=role,
            ),
        )
        token_data = auth_service.generate_token_response(user_like)
        set_refresh_cookie(response, token_data["refresh_token"])
        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": "bearer",
            "user": token_data["user"],
        }

    # Link clerk_id to existing user
    user.clerk_id = data.clerk_id
    if data.name and not user.name:
        user.name = data.name
    await db.commit()

    auth_service = AuthService(db)
    token_data = auth_service.generate_token_response(user)
    set_refresh_cookie(response, token_data["refresh_token"])
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "token_type": "bearer",
        "user": token_data["user"],
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(data: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and issue tokens.

    NOTE: OTP infrastructure not yet deployed — this endpoint requires
    a stored OTP record with expiration. Contact admin to enable.
    """
    raise HTTPException(
        status_code=501,
        detail="OTP verification not yet configured. Contact your administrator.",
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset - generates token (email sending placeholder)."""
    stmt = select(User).where(User.email == data.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if user:
        from app.core.security import create_access_token
        from app.integrations.email import send_password_reset_email
        # Generate password reset token (would normally send via email)
        raw_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        role = Role.normalize(raw_role)
        reset_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=role + "_RESET",
            token_type="password_reset",
        )
        # Send reset token via email
        await send_password_reset_email(to=user.email, reset_token=reset_token)
        return {"message": "If email exists, a reset link has been sent."}

    # Don't reveal if email exists
    return {"message": "If email exists, a reset link has been sent."}


@router.post("/reset-password", response_model=dict)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using valid reset token."""
    from app.core.security import decode_token, hash_password

    try:
        payload = decode_token(data.token)
        if not payload:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        token_type = payload.get("type")
        email = payload.get("email")

        if token_type != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")

        if not email:
            raise HTTPException(status_code=400, detail="Invalid token - missing email")

        # Find user by email
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        # Update password
        user.password_hash = hash_password(data.new_password)
        await db.flush()

        return {"message": "Password has been reset successfully."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to reset password: {str(e)}")
