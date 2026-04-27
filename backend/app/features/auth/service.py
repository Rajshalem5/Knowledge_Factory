"""Authentication business logic."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.auth.schemas import (
    CandidateRegisterRequest,
    LoginRequest,
    RefreshRequest,
)
from app.core.enums import Role


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, login_data: LoginRequest) -> tuple[Any, bool] | None:
        """Authenticate user or candidate. Returns (entity, is_candidate) or None."""
        # Check users table first
        stmt = select(User).where(User.email == login_data.email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user and verify_password(login_data.password, user.password_hash):
            return (user, False)

        # Check candidates table
        stmt = select(Candidate).where(Candidate.email == login_data.email)
        result = await self.db.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate and candidate.password_hash and verify_password(
            login_data.password, candidate.password_hash
        ):
            return (candidate, True)

        return None

    async def register_candidate(
        self, register_data: CandidateRegisterRequest, tenant_id: UUID, cycle_id: UUID
    ) -> Candidate:
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

    @staticmethod
    def generate_token_response(user_or_candidate: Any) -> dict:
        is_candidate = isinstance(user_or_candidate, Candidate)

        subject = str(user_or_candidate.id)
        tenant_id = str(user_or_candidate.tenant_id) if user_or_candidate.tenant_id else None
        role_val = user_or_candidate.role
        role = "CANDIDATE" if is_candidate else (role_val.value if hasattr(role_val, 'value') else str(role_val))

        access_token = create_access_token(subject=subject, tenant_id=tenant_id, role=role)
        refresh_tok = create_refresh_token(subject=subject)

        return {
            "access_token": access_token,
            "refresh_token": refresh_tok,
            "token_type": "bearer",
            "user": {
                "id": user_or_candidate.id,
                "email": user_or_candidate.email,
                "name": user_or_candidate.name,
                "role": role,
                "tenant_id": tenant_id,
            },
        }
