"""
Domain enumerations for the Knowledge Factory platform.

These enums are the single source of truth for all status values, roles,
and categorical fields used across ORM models, Pydantic schemas, and
service-layer validation.

Source: Knowledge_Factory_Technical_Architecture.docx, Section 5 & Table 21.
"""

import enum
import logging

logger = logging.getLogger(__name__)


# ── User / Staff ───────────────────────────────────────────────────

class Role(str, enum.Enum):
    """
    User roles for non-candidate humans (staff).
    Candidates do NOT use this enum — they have their own auth model.
    """
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    HR = "HR"
    INTERVIEWER = "INTERVIEWER"

    @classmethod
    def normalize(cls, raw: str | None) -> str:
        """
        Normalize any role string to its canonical uppercase form.
        Handles legacy/dirty formats (e.g. SUPERADMIN → SUPER_ADMIN).
        Unknown roles fall back to HR with a warning.
        """
        if not raw:
            logger.warning("[Role.normalize] Empty role, falling back to HR")
            return cls.HR.value

        cleaned = raw.strip().upper().replace(" ", "_")

        role_map = {
            "SUPERADMIN": cls.SUPER_ADMIN.value,
            "SUPER_ADMIN": cls.SUPER_ADMIN.value,
            "ADMIN": cls.ADMIN.value,
            "HR": cls.HR.value,
            "INTERVIEWER": cls.INTERVIEWER.value,
            "CANDIDATE": "CANDIDATE",
        }

        if cleaned in role_map:
            return role_map[cleaned]

        logger.warning(
            "[Role.normalize] Unknown role '%s' (cleaned: '%s'). Falling back to HR.",
            raw, cleaned,
        )
        return cls.HR.value


class UserStatus(str, enum.Enum):
    """Staff account status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


# ── Hiring Cycles ───────────────────────────────────────────────────

class CycleStatus(str, enum.Enum):
    """Hiring cycle lifecycle states."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


# ── Candidate State Machine ────────────────────────────────────────

class CandidateStatus(str, enum.Enum):
    """
    Candidate lifecycle states — strict FSM per architecture doc Table 21.

    State transitions:
        APPLIED       → ROUND1_PASSED, ROUND1_REJECTED, ROUND1_REVIEW
        ROUND1_REVIEW → ROUND1_PASSED, ROUND1_REJECTED
        ROUND1_PASSED → ROUND2_IN_PROGRESS
        ROUND2_IN_PROGRESS → ROUND2_PASSED, ROUND2_REJECTED, TERMINATED
        ROUND2_PASSED → ROUND3_IN_PROGRESS
        ROUND3_IN_PROGRESS → ROUND3_PASSED, ROUND3_REJECTED, TERMINATED
        ROUND3_PASSED → INTERVIEW_SCHEDULED
        INTERVIEW_SCHEDULED → INTERVIEW_COMPLETED
        INTERVIEW_COMPLETED → SELECTED, FINAL_REJECTED
        TERMINATED → (terminal)
    """
    APPLIED = "APPLIED"
    ROUND1_REVIEW = "ROUND1_REVIEW"
    ROUND1_PASSED = "ROUND1_PASSED"
    ROUND1_REJECTED = "ROUND1_REJECTED"
    ROUND2_IN_PROGRESS = "ROUND2_IN_PROGRESS"
    ROUND2_PASSED = "ROUND2_PASSED"
    ROUND2_REJECTED = "ROUND2_REJECTED"
    ROUND3_IN_PROGRESS = "ROUND3_IN_PROGRESS"
    ROUND3_PASSED = "ROUND3_PASSED"
    ROUND3_REJECTED = "ROUND3_REJECTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
    SELECTED = "SELECTED"
    FINAL_REJECTED = "FINAL_REJECTED"
    TERMINATED = "TERMINATED"

    @property
    def display_status(self) -> str:
        """Map granular backend status to simplified frontend-friendly status."""
        mapping = {
            CandidateStatus.APPLIED: "applied",
            CandidateStatus.ROUND1_REVIEW: "applied",
            CandidateStatus.ROUND1_PASSED: "eligible",
            CandidateStatus.ROUND1_REJECTED: "rejected",
            CandidateStatus.ROUND2_IN_PROGRESS: "round1",
            CandidateStatus.ROUND2_PASSED: "round1",
            CandidateStatus.ROUND2_REJECTED: "rejected",
            CandidateStatus.ROUND3_IN_PROGRESS: "round2",
            CandidateStatus.ROUND3_PASSED: "round2",
            CandidateStatus.ROUND3_REJECTED: "rejected",
            CandidateStatus.INTERVIEW_SCHEDULED: "round3",
            CandidateStatus.INTERVIEW_COMPLETED: "interviewed",
            CandidateStatus.SELECTED: "selected",
            CandidateStatus.FINAL_REJECTED: "rejected",
            CandidateStatus.TERMINATED: "rejected",
        }
        return mapping.get(self, "applied")

    @classmethod
    def from_display_status(cls, display: str) -> "CandidateStatus | None":
        """Map a simplified frontend status back to the most appropriate backend status."""
        reverse_map = {
            "applied": cls.APPLIED,
            "eligible": cls.ROUND1_PASSED,
            "round1": cls.ROUND2_IN_PROGRESS,
            "round2": cls.ROUND3_IN_PROGRESS,
            "round3": cls.INTERVIEW_SCHEDULED,
            "interviewed": cls.INTERVIEW_COMPLETED,
            "selected": cls.SELECTED,
            "rejected": cls.FINAL_REJECTED,
        }
        return reverse_map.get(display.lower())


# ── Assessments ────────────────────────────────────────────────────

class AssessmentRound(str, enum.Enum):
    """Assessment round identifiers (stored as VARCHAR(10))."""
    ROUND_2 = "ROUND_2"
    ROUND_3 = "ROUND_3"


class AssessmentStatus(str, enum.Enum):
    """Status of an individual assessment session."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"


class SubmissionSection(str, enum.Enum):
    """Types of assessment submission sections."""
    CODING = "CODING"
    MCQ = "MCQ"
    USECASE = "USECASE"


# ── Scores ─────────────────────────────────────────────────────────

class ScoreVerdict(str, enum.Enum):
    """Score verdict for a round."""
    PASS = "PASS"
    FAIL = "FAIL"


# ── Interviews ─────────────────────────────────────────────────────

class InterviewRecommendation(str, enum.Enum):
    """Interviewer's final recommendation."""
    SELECT = "SELECT"
    REJECT = "REJECT"
    HOLD = "HOLD"


# ── Proctoring ─────────────────────────────────────────────────────

class ProctoringEventType(str, enum.Enum):
    """Types of proctoring events detected client-side or server-side."""
    TAB_SWITCH = "tab_switch"
    FACE_NOT_DETECTED = "face_not_detected"
    MULTIPLE_FACES = "multiple_faces"
    COPY_PASTE = "copy_paste"
    PHONE_DETECTED = "phone_detected"
    RIGHT_CLICK = "right_click"


class ProctoringSeverity(str, enum.Enum):
    """Severity levels for proctoring events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Organization / SaaS ────────────────────────────────────────────

class OrganizationPlan(str, enum.Enum):
    """SaaS subscription plan tiers."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# ── Misc ────────────────────────────────────────────────────────────

class ProblemDifficulty(str, enum.Enum):
    """Difficulty level for assessment problems."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class EvaluationRecommendation(str, enum.Enum):
    """AI/System recommendation based on composite score."""
    STRONGLY_RECOMMENDED = "STRONGLY_RECOMMENDED"
    RECOMMENDED = "RECOMMENDED"
    BORDERLINE = "BORDERLINE"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
