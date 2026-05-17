"""
Central model registry — imports all models eagerly so SQLAlchemy's mapper
can resolve cross-model relationship() string references at runtime.

Each model file uses TYPE_CHECKING to break circular import cycles for type
annotations. But relationship() string references like "Assessment" or
"Candidate" must resolve in Base.registry at mapper configuration time.
This module is the single import site that registers everything.

Import once at app startup (or at the bottom of database.py after Base is defined).
"""
from __future__ import annotations

# Import every model module. The act of importing registers its classes
# with Base's registry, making string-based relationships resolvable.
from app.features.auth.models import User  # noqa: F401
from app.features.candidates.models import Candidate  # noqa: F401
from app.features.assessments.models import Assessment, Submission, Score  # noqa: F401
from app.features.hiring_cycles.models import HiringCycle  # noqa: F401
from app.features.proctoring.models import ProctoringRecord  # noqa: F401
from app.features.interviews.models import InterviewFeedback  # noqa: F401
from app.features.audit.models import AuditLog  # noqa: F401
from app.features.analytics.models import AIGenerationLog  # noqa: F401
from app.features.notifications.models import EmailLog  # noqa: F401
