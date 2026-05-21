"""Authentication business logic - simplified without multi-tenancy."""

import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

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

    async def authenticate(self, login_data: LoginRequest) -> tuple[Any, bool] | None:
        """Authenticate user or candidate. Returns (entity, is_candidate) or None."""
        logger.debug("Attempting authentication for email: %s", login_data.email)

        # Check users table first
        stmt = select(User).where(User.email == login_data.email)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if user:
            logger.debug("Found user in users table. Verifying password...")
            if verify_password(login_data.password, user.password_hash):
                logger.info("User authentication successful: %s", login_data.email)
                return (user, False)
            else:
                logger.warning("User authentication failed (password mismatch): %s", login_data.email)
        else:
            logger.debug("User not found in users table: %s", login_data.email)

        # Check candidates table
        stmt = select(Candidate).where(Candidate.email == login_data.email)
        result = await self.db.execute(stmt)
        candidate = result.scalars().first()

        if candidate:
            logger.debug("Found candidate in candidates table. Verifying password...")
            if candidate.password_hash and verify_password(
                login_data.password, candidate.password_hash
            ):
                logger.info("Candidate authentication successful: %s", login_data.email)
                return (candidate, True)
            else:
                logger.warning("Candidate authentication failed (password mismatch or no hash): %s", login_data.email)
        else:
            logger.debug("Candidate not found in candidates table: %s", login_data.email)

        return None

    async def register_candidate(
        self, register_data: CandidateRegisterRequest, cycle_id: str
    ) -> Candidate:
        """Register a new candidate."""
        from app.config import settings
        
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
            email_verified=not settings.ENABLE_EMAIL_VERIFICATION, # auto-verify if disabled
        )
        self.db.add(new_candidate)
        await self.db.flush()
        return new_candidate

    @staticmethod
    def generate_token_response(user_or_candidate: Any) -> dict:
        """Generate token response with user info.
        Role is always normalized to canonical uppercase form before embedding in JWT.
        """
        from app.features.candidates.models import Candidate

        is_candidate = isinstance(user_or_candidate, Candidate)

        subject = str(user_or_candidate.id)
        email = user_or_candidate.email

        if is_candidate:
            role = "CANDIDATE"
        else:
            raw_role = user_or_candidate.role.value if hasattr(user_or_candidate.role, 'value') else str(user_or_candidate.role)
            role = Role.normalize(raw_role)
            logger.debug("generate_token_response: role %s → %s for %s", raw_role, role, email)

        access_token = create_access_token(subject=subject, email=email, role=role)
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
            },
        }
