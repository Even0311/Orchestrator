from typing import List, Optional
from pydantic import BaseModel, Field


class Risk(BaseModel):
    description: str
    severity: str = Field(default="medium", pattern="^(low|medium|high)$")
    mitigation: Optional[str] = None


class Progress(BaseModel):
    item: str
    completed: bool = False


class WorkingState(BaseModel):
    project_name: str
    current_phase: str
    current_goal: str
    next_expected_step: str
    recent_progress: List[Progress] = Field(default_factory=list)
    current_risks: List[Risk] = Field(default_factory=list)
    context_notes: Optional[str] = None
    last_updated: Optional[str] = None
