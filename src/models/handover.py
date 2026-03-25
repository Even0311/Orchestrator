from typing import List, Optional
from pydantic import BaseModel, Field

from .working_state import Risk, Progress
from .decision_log import DecisionEntry


class HandoverPacket(BaseModel):
    generated_at: str
    project_name: str
    charter_excerpt: str
    core_principles: List[str] = Field(default_factory=list)
    current_phase: str
    current_goal: str
    recent_progress: List[Progress] = Field(default_factory=list)
    current_risks: List[Risk] = Field(default_factory=list)
    next_expected_step: str
    recent_decisions: List[DecisionEntry] = Field(default_factory=list)
    context_notes: Optional[str] = None
