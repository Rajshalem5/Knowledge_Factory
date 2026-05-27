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
        self, register_data: CandidateRegisterRequest, cycle_id: str, resume: Any | None = None
    ) -> Candidate:
        """Register a new candidate with optional resume parsing and auto-screening."""
        from app.config import settings
        from app.features.hiring_cycles.models import HiringCycle
        from app.features.selection.service import EvaluationService
        from app.services.parser import extract_text_from_file
        from app.services.extractor import extract_candidate_info
        from app.core.branch_utils import is_branch_eligible
        from app.core.enums import CandidateStatus
        import uuid
        import os
        from datetime import datetime

        # Check for duplicate email
        stmt = select(Candidate).where(Candidate.email == register_data.email)
        result = await self.db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise ValueError(
                f"A candidate with email '{register_data.email}' is already registered."
            )

        # Get cycle for screening config
        stmt = select(HiringCycle).where(HiringCycle.id == cycle_id)
        res = await self.db.execute(stmt)
        cycle = res.scalar_one_or_none()
        if not cycle:
            raise ValueError("Hiring cycle not found")

        # Initial creation
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
            email_verified=not settings.ENABLE_EMAIL_VERIFICATION,
            status=CandidateStatus.APPLIED
        )

        # Handle Resume if provided
        if resume:
            try:
                # 1. Save file to disk
                content = await resume.read()
                filename = f"resume_{uuid.uuid4().hex[:8]}{os.path.splitext(resume.filename)[1]}"
                upload_dir = "uploads/resumes"
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, filename)
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                new_candidate.resume_url = f"uploads/resumes/{filename}"

                # 2. Extract info via AI
                raw_text = await extract_text_from_file(content, filename)
                extracted = await extract_candidate_info(raw_text)
                
                # 3. Enrich profile (if fields were empty in registration)
                if extracted.get("name") and new_candidate.name in ["", "Unnamed Candidate"]:
                    new_candidate.name = extracted["name"]
                
                if extracted.get("college") and not new_candidate.college:
                    new_candidate.college = extracted["college"]
                    
                if extracted.get("branch") and not new_candidate.branch:
                    new_candidate.branch = extracted["branch"]
                    
                if extracted.get("degree"):
                    new_candidate.degree = extracted["degree"]
                    
                if extracted.get("cgpa") and new_candidate.cgpa == 0:
                    try:
                        new_candidate.cgpa = float(extracted["cgpa"])
                    except: pass
                        
                if extracted.get("graduation_year") and new_candidate.passed_out_year == 0:
                    try:
                        new_candidate.passed_out_year = int(extracted["graduation_year"])
                    except: pass
                
                if extracted.get("skills"):
                    skills = extracted["skills"]
                    new_candidate.skills = ", ".join(skills) if isinstance(skills, list) else skills

                # Update custom fields
                new_candidate.custom_fields = {
                    "percentage": extracted.get("percentage"),
                    "academic_status": extracted.get("academic_status"),
                    "experience_summary": extracted.get("experience_summary"),
                }
            except Exception as e:
                logger.error(f"AI parsing failed during registration for {register_data.email}: {e}")

        # 4. Auto-screening
        cfg = cycle.eligibility_config or {}
        def check_eligibility(cand_obj):
            min_cgpa = float(cfg.get("min_cgpa", 6.0))
            allowed_branches = cfg.get("allowed_branches", [])
            allowed_degrees = cfg.get("allowed_degrees", [])
            allowed_years = cfg.get("passed_out_years", [])

            cgpa_ok = float(cand_obj.cgpa) >= min_cgpa
            branch_ok = is_branch_eligible(cand_obj.branch, allowed_branches)
            degree_ok = not allowed_degrees or (cand_obj.degree and cand_obj.degree.lower() in [d.lower() for d in allowed_degrees])
            year_ok = not allowed_years or cand_obj.passed_out_year in allowed_years

            return cgpa_ok and branch_ok and degree_ok and year_ok

        new_candidate.status = CandidateStatus.ROUND1_PASSED if check_eligibility(new_candidate) else CandidateStatus.ROUND1_REJECTED
        
        self.db.add(new_candidate)
        await self.db.flush()

        # 5. Update evaluation metrics
        eval_svc = EvaluationService(self.db)
        await eval_svc.update_candidate_evaluation(new_candidate.id)
        
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
