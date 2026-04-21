"""
Authentication routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.features.auth.schemas import LoginRequest, CandidateRegisterRequest, Token, UserRead
from app.features.auth.service import AuthService
from app.features.auth.models import Tenant
from app.features.hiring_cycles.models import HiringCycle

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user/candidate and return JWT.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate(login_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    return auth_service.generate_token_response(user)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_candidate(
    register_data: CandidateRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new candidate for the active hiring cycle.
    """
    tenant_stmt = select(Tenant).limit(1)
    tenant_res = await db.execute(tenant_stmt)
    tenant = tenant_res.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=500, detail="No tenant configured in system")
        
    cycle_stmt = select(HiringCycle).where(HiringCycle.tenant_id == tenant.id).limit(1)
    cycle_res = await db.execute(cycle_stmt)
    cycle = cycle_res.scalar_one_or_none()
    
    if not cycle:
        raise HTTPException(status_code=500, detail="No active hiring cycle found")

    auth_service = AuthService(db)
    
    try:
        candidate = await auth_service.register_candidate(register_data, tenant.id, cycle.id)
        return auth_service.generate_token_response(candidate)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserRead)
async def get_me(current_user=Depends(get_current_user)):
    """
    Get current user profile from JWT.
    """
    return current_user
