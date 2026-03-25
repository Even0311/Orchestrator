from typing import List, Optional
from pydantic import BaseModel, Field

from .working_state import Risk, Progress
from .decision_log import DecisionEntry


class RunSummary(BaseModel):
    task_summary: str
    status: str
    files_changed: List[str] = Field(default_factory=list)
    implemented_items: List[str] = Field(default_factory=list)
    tests_run: List[str] = Field(default_factory=list)
    unresolved_items: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ReviewPacket(BaseModel):
    generated_at: str
    project_name: str
    current_phase: str
    current_goal: str
    project_summary: str
    recent_progress: List[Progress] = Field(default_factory=list)
    current_risks: List[Risk] = Field(default_factory=list)
    recent_decisions: List[DecisionEntry] = Field(default_factory=list)
    run_summary: RunSummary
    inspect_next: str
