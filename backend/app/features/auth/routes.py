"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.features.auth.schemas import (
    CandidateRegisterRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OtpVerifyRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
)
from app.features.auth.service import AuthService
from app.features.hiring_cycles.models import HiringCycle

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    result = await auth_service.authenticate(login_data)

    if not result:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user_or_candidate, _is_candidate = result
    return auth_service.generate_token_response(user_or_candidate)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_candidate(
    register_data: CandidateRegisterRequest, db: AsyncSession = Depends(get_db)
):
    stmt = select(HiringCycle).limit(1)
    res = await db.execute(stmt)
    cycle = res.scalar_one_or_none()

    if not cycle:
        raise HTTPException(
            status_code=500,
            detail="No active hiring cycle. Contact admin.",
        )

    auth_service = AuthService(db)

    try:
        candidate = await auth_service.register_candidate(
            register_data, cycle.tenant_id, cycle.id
        )
        return auth_service.generate_token_response(candidate)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    is_candidate = hasattr(current_user, "college")
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": "CANDIDATE" if is_candidate else current_user.role.value,
        "tenant_id": str(current_user.tenant_id) if current_user.tenant_id else None,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from app.core.security import decode_token

    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    sub = payload["sub"]

    # Resolve entity
    stmt = select(Candidate).where(Candidate.id == sub)
    res = await db.execute(stmt)
    candidate = res.scalar_one_or_none()

    if not candidate:
        stmt = select(User).where(User.id == sub)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        auth_svc = AuthService(db)
        return auth_svc.generate_token_response(user)

    auth_svc = AuthService(db)
    return auth_svc.generate_token_response(candidate)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user=Depends(get_current_user)):
    """Client-side token removal; server-side invalidation via blacklist to be added later."""
    return None


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(data: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Placeholder — OTP generation and verification logic pending."""
    # For MVP dev: accept any 6-digit OTP for registered emails
    stmt = select(User).where(User.email == data.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Email not registered")

    # Dev-mode: auto-accept any OTP
    if user.password_hash and len(data.otp) == 6:
        access_token = create_access_token(subject=str(user.id), tenant_id=str(user.tenant_id) if user.tenant_id else None, role=user.role.value)
        refresh_tok = create_refresh_token(subject=str(user.id))
        return {
            "access_token": access_token,
            "refresh_token": refresh_tok,
            "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role.value, "tenant_id": str(user.tenant_id) if user.tenant_id else None},
        }

    raise HTTPException(status_code=400, detail="OTP expired or invalid")


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Placeholder — sends password reset email with token."""
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Placeholder — validates reset token and updates password."""
    return {"message": "Password has been reset."}


# Re-import for verify-otp route
from app.core.security import create_access_token, create_refresh_token
