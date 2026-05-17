"""Analytics schemas — snake_case fields matching frontend types."""

from typing import Any
from pydantic import BaseModel


class FunnelResponse(BaseModel):
    applied: int = 0
    eligible: int = 0
    assessed: int = 0
    interviewed: int = 0
    selected: int = 0


class PassRateItem(BaseModel):
    round: str
    pass_rate: float


class CollegeBreakdownItem(BaseModel):
    college: str
    count: int
    avg_score: float


class BranchPerformanceItem(BaseModel):
    branch: str
    count: int
    avg_score: float


class ProctoringViolationItem(BaseModel):
    type: str
    count: int


class DashboardResponse(BaseModel):
    total_candidates: int
    selected_count: int
    select_rate: float
    avg_cgpa: float
    status_breakdown: dict[str, Any]
    pass_rate_per_round: list[PassRateItem] = []
    college_breakdown: list[CollegeBreakdownItem] = []
    branch_performance: list[BranchPerformanceItem] = []
    proctoring_violations: list[ProctoringViolationItem] = []


class OrganizationRead(BaseModel):
    id: str
    name: str
    slug: str
    plan: str = "starter"
    candidate_count: int = 0
    active_hiring_cycles: int = 0
    status: str = "ACTIVE"

    class Config:
        from_attributes = True
