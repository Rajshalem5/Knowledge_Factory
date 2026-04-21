"""
Authentication business logic.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.auth.schemas import CandidateRegisterRequest, LoginRequest
from app.core.enums import Role


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, login_data: LoginRequest) -> Any | None:
        """
        Authenticate a user or candidate.
        First checks users table, then candidates table.
        """
        # 1. Check users (Staff)
        user_stmt = select(User).where(User.email == login_data.email)
        result = await self.db.execute(user_stmt)
        user = result.scalar_one_or_none()

        if user and verify_password(login_data.password, user.password_hash):
            return user

        # 2. Check candidates
        cand_stmt = select(Candidate).where(Candidate.email == login_data.email)
        result = await self.db.execute(cand_stmt)
        candidate = result.scalar_one_or_none()

        if candidate and candidate.password_hash and verify_password(login_data.password, candidate.password_hash):
            # Map candidate to a pseudo-user object for token generation
            # or just return candidate and handle downstream
            return candidate

        return None

    async def register_candidate(self, register_data: CandidateRegisterRequest, tenant_id: UUID, cycle_id: UUID) -> Candidate:
        """Register a new candidate."""
        new_candidate = Candidate(
            tenant_id=tenant_id,
            cycle_id=cycle_id,
            email=register_data.email,
            password_hash=hash_password(register_data.password),
            name=register_data.name,
            college=register_data.college,
            branch=register_data.branch,
            cgpa=register_data.cgpa,
            passed_out_year=register_data.passed_out_year,
            language_choice=register_data.language_choice,
        )
        self.db.add(new_candidate)
        await self.db.flush()
        return new_candidate

    def generate_token_response(self, user_or_candidate: Any) -> dict:
        """Generate JWT response for a validated user/candidate."""
        is_candidate = isinstance(user_or_candidate, Candidate)
        
        subject = user_or_candidate.id
        tenant_id = user_or_candidate.tenant_id
        role = "CANDIDATE" if is_candidate else user_or_candidate.role
        
        access_token = create_access_token(
            subject=subject,
            tenant_id=tenant_id,
            role=role
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_or_candidate.id,
                "email": user_or_candidate.email,
                "name": user_or_candidate.name,
                "role": role,
                "tenant_id": tenant_id
            }
        }
