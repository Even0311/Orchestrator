from typing import List
from pydantic import BaseModel, Field

ESCALATION_CATEGORIES = {
    "implementation_blocked",
    "state_conflict_detected",
    "decision_required",
    "review_attention_required",
    "none",
}

CATEGORY_SEVERITY = {
    "implementation_blocked": "high",
    "state_conflict_detected": "high",
    "decision_required": "medium",
    "review_attention_required": "low",
    "none": "none",
}


class EscalationEvidence(BaseModel):
    artifact_status: str
    unresolved_items: List[str] = Field(default_factory=list)
    relevant_risks: List[str] = Field(default_factory=list)
    proposal_sections: List[str] = Field(default_factory=list)


class EscalationPacket(BaseModel):
    generated_at: str
    project_name: str
    category: str
    severity: str
    why_now: str
    evidence: EscalationEvidence
    recommended_human_action: str
    explicitly_not_decided_by_system: List[str] = Field(default_factory=list)
