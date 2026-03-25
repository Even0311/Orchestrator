from typing import Optional
from pydantic import BaseModel, Field

ROUND_STATUSES = (
    "created",
    "task_ready",
    "run_received",
    "review_ready",
    "proposal_ready",
    "escalation_ready",
    "awaiting_human_approval",
    "closed",
)

_STATUS_PATTERN = "^(" + "|".join(ROUND_STATUSES) + ")$"


class RoundState(BaseModel):
    round_id: str
    project_name: str
    created_at: str
    status: str = Field(pattern=_STATUS_PATTERN)
    source_task_role: str
    based_on_phase: str
    based_on_goal: str
    # artifact presence flags
    has_run_artifact: bool = False
    has_review_packet: bool = False
    has_proposal: bool = False
    has_escalation: bool = False
    # optional detail fields
    latest_run_artifact: Optional[str] = None
    escalation_category: Optional[str] = None
    updated_at: Optional[str] = None
    notes: Optional[str] = None
