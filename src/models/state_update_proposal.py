from typing import List, Optional
from pydantic import BaseModel, Field


class ProposalBasis(BaseModel):
    artifact_path: str
    review_packet_path: str


class StateUpdateProposal(BaseModel):
    generated_at: str
    project_name: str
    based_on: ProposalBasis

    # Additions: new completed progress items from implemented_items
    proposed_recent_progress_additions: List[str] = Field(default_factory=list)

    # Updates: existing pending progress items suggested for completion
    # Kept empty by default; human decides which pending items to close
    proposed_recent_progress_updates: List[str] = Field(default_factory=list)

    # Optional field-level suggestions
    proposed_current_goal_update: Optional[str] = None
    proposed_next_expected_step_update: Optional[str] = None

    # Suggested new or updated risks (as descriptive strings)
    proposed_risk_updates: List[str] = Field(default_factory=list)

    # Candidate decision log entries (descriptive strings only, not full entries)
    proposed_decision_log_candidates: List[str] = Field(default_factory=list)

    # Fields explicitly left unchanged (explains what was NOT proposed)
    explicitly_unchanged: List[str] = Field(default_factory=list)

    # Short explanations for non-obvious proposal choices
    rationale_notes: List[str] = Field(default_factory=list)
