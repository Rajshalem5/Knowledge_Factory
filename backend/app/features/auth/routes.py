"""Authentication routes - simplified without multi-tenancy."""

from fastapi import APIRouter, Depends, HTTPException, status
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
    TokenResponse,
    UserResponse,
)
from app.features.auth.service import AuthService
from app.features.candidates.models import Candidate
from app.features.auth.models import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user or candidate and return tokens."""
    auth_service = AuthService(db)
    result = await auth_service.authenticate(login_data)

    if not result:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user_or_candidate, _is_candidate = result
    return auth_service.generate_token_response(user_or_candidate)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_candidate(
    register_data: CandidateRegisterRequest, db: AsyncSession = Depends(get_db)
):
    """Register a new candidate."""
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

    try:
        candidate = await auth_service.register_candidate(register_data, cycle.id)
        return auth_service.generate_token_response(candidate)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Get current user profile."""
    is_candidate = isinstance(current_user, Candidate)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role="CANDIDATE" if is_candidate else current_user.role,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    from app.core.security import decode_token

    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    sub = payload["sub"]

    # Resolve entity - check candidates first, then users
    stmt = select(Candidate).where(Candidate.id == sub)
    res = await db.execute(stmt)
    candidate = res.scalar_one_or_none()

    if candidate:
        auth_svc = AuthService(db)
        return auth_svc.generate_token_response(candidate)

    stmt = select(User).where(User.id == sub)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    auth_svc = AuthService(db)
    return auth_svc.generate_token_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user=Depends(get_current_user)):
    """Logout - client removes token, server will add blacklist in future."""
    return None


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(data: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and issue tokens (dev mode accepts any 6-digit code)."""
    from app.core.security import create_access_token, create_refresh_token
    
    stmt = select(User).where(User.email == data.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Email not registered")

    # Dev-mode: auto-accept any 6-digit OTP
    if user.password_hash and len(data.otp) == 6:
        access_token = create_access_token(subject=str(user.id), email=user.email, role=user.role)
        refresh_tok = create_refresh_token(subject=str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_tok,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
            ),
        )

    raise HTTPException(status_code=400, detail="OTP expired or invalid")


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset - generates token (email sending placeholder)."""
    stmt = select(User).where(User.email == data.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if user:
        from app.core.security import create_access_token
        # Generate password reset token (would normally send via email)
        reset_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role + "_RESET"
        )
        # TODO: Send reset_token via email
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
        await db.commit()
        
        return {"message": "Password has been reset successfully."}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to reset password: {str(e)}")
