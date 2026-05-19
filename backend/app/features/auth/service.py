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

# ── XSS prevention: sanitize user-supplied text fields ──────────
import nh3


def _sanitize_text(value: str | None, max_length: int = 200) -> str:
    """Sanitize user-supplied text: strip tags, trim, enforce length.
    
    Follows the Three-Tier Boundary System from addyosmani/agent-skills:
    'Validate all external input at the system boundary.'
    """
    if not value:
        return ""
    cleaned = nh3.clean(value)
    return cleaned.strip()[:max_length]


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, login_data: LoginRequest) -> tuple[Any, bool] | None:
        """Authenticate user or candidate. Returns (entity, is_candidate) or None."""
        # Check users table first
        stmt = select(User).where(User.email == login_data.email)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if user and verify_password(login_data.password, user.password_hash):
            return (user, False)

        # Check candidates table
        stmt = select(Candidate).where(Candidate.email == login_data.email)
        result = await self.db.execute(stmt)
        candidate = result.scalars().first()

        if candidate and candidate.password_hash and verify_password(
            login_data.password, candidate.password_hash
        ):
            return (candidate, True)

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
            name=_sanitize_text(register_data.name),
            college=_sanitize_text(register_data.college),
            branch=_sanitize_text(register_data.branch, max_length=50),
            cgpa=register_data.cgpa,
            passed_out_year=register_data.passed_out_year,
            language_choice=register_data.language_choice,
        )
        self.db.add(new_candidate)
        await self.db.flush()
        return new_candidate

    @staticmethod
    def generate_token_response(user_or_candidate: Any) -> dict:
        """Generate token response with user info."""
        from app.features.candidates.models import Candidate
        
        is_candidate = isinstance(user_or_candidate, Candidate)

        subject = str(user_or_candidate.id)
        email = user_or_candidate.email
        role = "CANDIDATE" if is_candidate else (user_or_candidate.role.value if hasattr(user_or_candidate.role, 'value') else str(user_or_candidate.role))

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

    async def update_profile(self, user_id: str, name: str) -> dict:
        """Update name for either a User or Candidate. Returns updated profile."""
        # Try User table first (staff)
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.name = _sanitize_text(name)
            await self.db.flush()
            return {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                "photo_url": user.photo_url,
                "status": user.status.value if hasattr(user.status, "value") else str(user.status),
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

        # Try Candidate table
        stmt = select(Candidate).where(Candidate.id == user_id)
        result = await self.db.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate:
            candidate.name = _sanitize_text(name)
            await self.db.flush()
            return {
                "id": str(candidate.id),
                "email": candidate.email,
                "name": candidate.name,
                "role": "CANDIDATE",
                "photo_url": candidate.photo_url,
                "status": None,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            }

        raise ValueError("User not found")

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """Verify current password and update to new password."""
        # Check User table
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            if not verify_password(current_password, user.password_hash):
                raise ValueError("Current password is incorrect")
            user.password_hash = hash_password(new_password)
            await self.db.flush()
            return

        # Check Candidate table
        stmt = select(Candidate).where(Candidate.id == user_id)
        result = await self.db.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate:
            if not verify_password(current_password, candidate.password_hash):
                raise ValueError("Current password is incorrect")
            candidate.password_hash = hash_password(new_password)
            await self.db.flush()
            return

        raise ValueError("User not found")

    async def get_profile(self, user_id: str) -> dict:
        """Get full profile for a user (staff or candidate)."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                "photo_url": user.photo_url,
                "status": user.status.value if hasattr(user.status, "value") else str(user.status),
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

        stmt = select(Candidate).where(Candidate.id == user_id)
        result = await self.db.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate:
            return {
                "id": str(candidate.id),
                "email": candidate.email,
                "name": candidate.name,
                "role": "CANDIDATE",
                "photo_url": candidate.photo_url,
                "status": None,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            }

        raise ValueError("User not found")
