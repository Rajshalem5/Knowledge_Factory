"""Analytics schemas."""

from typing import Any
from pydantic import BaseModel


class FunnelResponse(BaseModel):
    applied: int
    eligible: int
    assessed: int
    interviewed: int
    selected: int


class DashboardResponse(BaseModel):
    total_candidates: int
    selected_count: int
    select_rate: float
    avg_cgpa: float
    status_breakdown: dict[str, Any]


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
