from typing import List, Optional
from pydantic import BaseModel, Field

from .working_state import Risk, Progress
from .decision_log import DecisionEntry

SUPPORTED_ROLES = {"claude", "reviewer", "decision_maker"}


class TaskPacket(BaseModel):
    generated_at: str
    role: str
    project_name: str
    current_phase: str
    current_goal: str

    # Shared optional fields
    next_expected_step: Optional[str] = None
    context_notes: Optional[str] = None
    recent_progress: Optional[List[Progress]] = None
    current_risks: Optional[List[Risk]] = None
    recent_decisions: Optional[List[DecisionEntry]] = None

    # Claude-specific
    implementation_boundaries: Optional[List[str]] = None

    # Reviewer-specific
    project_summary: Optional[str] = None
    inspect_next: Optional[str] = None

    # Decision-maker-specific
    decision_needed: Optional[str] = None
    why_now: Optional[str] = None
