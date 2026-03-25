from typing import List, Optional
from pydantic import BaseModel, Field

VALID_STATUSES = {"success", "partial", "failed"}


class ImplementationRunArtifact(BaseModel):
    project_name: str
    generated_at: str
    role: str
    task_summary: str
    status: str = Field(pattern="^(success|partial|failed)$")
    files_changed: List[str] = Field(default_factory=list)
    implemented_items: List[str] = Field(default_factory=list)
    tests_run: List[str] = Field(default_factory=list)
    unresolved_items: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
