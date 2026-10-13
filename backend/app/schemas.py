from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

class QLEEnrollmentRequest(BaseModel):
    participant_id: int
    plan_id: int
    qle_type: str = Field(pattern="^(MARRIAGE|BIRTH|LOSS_OF_COVERAGE|OPEN_ENROLLMENT)$")
    event_date: date
    submitted_date: date
    target_coverage_tier: str = Field(pattern="^(EE_ONLY|EE_SPOUSE|EE_CHILD|EE_FAMILY)$")
    include_dependent_ids: List[int] = Field(default_factory=list)
    annual_hsa_contribution: Decimal = Field(default=Decimal("0.00"), ge=0)

class ElectionSnapshot(BaseModel):
    coverage_tier: Optional[str] = None
    per_paycheck_deduction: Optional[Decimal] = None
    annual_hsa_contribution: Optional[Decimal] = None
    effective_date: Optional[date] = None
    status: Optional[str] = None

class QLEEnrollmentResponse(BaseModel):
    qle_status: str
    message: str
    participant_name: str
    before_state: ElectionSnapshot
    after_state: ElectionSnapshot

class SeedRequest(BaseModel):
    scenario: str = Field(default="all", pattern="^(all|open_enrollment|qle_life_events|dependent_age_out)$")
