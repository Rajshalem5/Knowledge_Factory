"""Analytics schemas."""

from typing import Any
from pydantic import BaseModel, ConfigDict


class FunnelResponse(BaseModel):
    applied: int = 0
    eligible: int = 0
    assessed: int = 0
    interviewed: int = 0
    selected: int = 0


class PassRatePerRound(BaseModel):
    round: str
    pass_rate: float


class CollegeBreakdown(BaseModel):
    college: str
    count: int
    avg_score: float = 0.0


class BranchPerformance(BaseModel):
    branch: str
    count: int
    avg_score: float = 0.0


class ProctoringViolation(BaseModel):
    type: str
    count: int


class DashboardResponse(BaseModel):
    total_candidates: int
    selected_count: int
    select_rate: float
    avg_cgpa: float
    status_breakdown: dict[str, Any]
    pass_rate_per_round: list[PassRatePerRound] = []
    college_breakdown: list[CollegeBreakdown] = []
    branch_performance: list[BranchPerformance] = []
    proctoring_violations: list[ProctoringViolation] = []


class OrganizationRead(BaseModel):
    id: str
    name: str
    slug: str
    plan: str = "starter"
    candidate_count: int = 0
    active_hiring_cycles: int = 0
    status: str = "ACTIVE"

    model_config = ConfigDict(from_attributes=True)
