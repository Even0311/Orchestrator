from typing import List, Optional
from pydantic import BaseModel, Field


class DecisionEntry(BaseModel):
    date: str
    title: str
    decision: str
    rationale: str
    alternatives_considered: Optional[List[str]] = None
    impact: Optional[str] = None


class DecisionLog(BaseModel):
    decisions: List[DecisionEntry] = Field(default_factory=list)
