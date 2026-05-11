"""Authentication business logic - simplified without multi-tenancy."""

from typing import Any
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
from app.features.auth.schemas import (
    CandidateRegisterRequest,
    LoginRequest,
)
from app.core.enums import Role


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, login_data: LoginRequest) -> User | None:
        """Authenticate user or candidate. Returns User or None."""
        # Check users table first
        stmt = select(User).where(User.email == login_data.email)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if user and user.password_hash and verify_password(login_data.password, user.password_hash):
            return user

        # Check candidates table
        from app.features.candidates.models import Candidate
        stmt = select(Candidate).where(Candidate.email == login_data.email)
        result = await self.db.execute(stmt)
        candidate = result.scalars().first()

        if candidate and candidate.password_hash and verify_password(login_data.password, candidate.password_hash):
            # Convert candidate to user-like object for token generation
            user_like = User(
                id=candidate.id,
                email=candidate.email,
                name=candidate.name,
                role="CANDIDATE",  # Set role as CANDIDATE
                password_hash=candidate.password_hash
            )
            return user_like

        return None

    async def register_candidate(
        self, register_data: CandidateRegisterRequest, cycle_id: str
    ) -> Candidate:
        """Register a new candidate."""
        # Check for duplicate email
        stmt = select(Candidate).where(Candidate.email == register_data.email)
        result = await self.db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise ValueError(
                f"A candidate with email '{register_data.email}' is already registered."
            )

        new_candidate = Candidate(
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
    def generate_token_response(user: User) -> dict:
        """Generate token response with user info."""
        subject = str(user.id)
        email = user.email
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)

        access_token = create_access_token(subject=subject, email=email, role=role)
        refresh_tok = create_refresh_token(subject=subject)

        return {
            "access_token": access_token,
            "refresh_token": refresh_tok,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,  # This maps to full_name column
                "role": role,
            },
        }
