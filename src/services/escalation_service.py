import json
from datetime import datetime, timezone
from pathlib import Path

from src.models import (
    EscalationPacket,
    EscalationEvidence,
    ImplementationRunArtifact,
    StateUpdateProposal,
    CATEGORY_SEVERITY,
)
from .file_reader import FileReader
from .ingestion_service import load_artifact, IngestionError
from .review_service import select_latest_artifact, ReviewError
from .proposal_service import ProposalError


class EscalationError(Exception):
    pass


# ---------------------------------------------------------------------------
# Proposal loader
# ---------------------------------------------------------------------------

def load_state_update_proposal(state_dir: Path) -> StateUpdateProposal:
    path = state_dir / "state_update_proposal.json"
    if not path.exists():
        raise EscalationError(
            f"state_update_proposal.json not found in {state_dir}. "
            "Run 'generate-state-update-proposal' first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return StateUpdateProposal(**data)


# ---------------------------------------------------------------------------
# Deterministic trigger rules
# Precedence (highest → lowest):
#   implementation_blocked > state_conflict_detected > decision_required
#   > review_attention_required > none
# ---------------------------------------------------------------------------

def _is_implementation_blocked(artifact: ImplementationRunArtifact) -> bool:
    """Run failed outright, or partial with no progress and open blockers."""
    if artifact.status == "failed":
        return True
    if (
        artifact.status == "partial"
        and not artifact.implemented_items
        and artifact.unresolved_items
    ):
        return True
    return False


def _is_state_conflict(artifact: ImplementationRunArtifact, proposal: StateUpdateProposal) -> bool:
    """Phase-complete claim (goal update proposed) conflicts with new risk evidence."""
    return (
        proposal.proposed_current_goal_update is not None
        and len(proposal.proposed_risk_updates) > 0
    )


def _is_decision_required(proposal: StateUpdateProposal) -> bool:
    """Decision candidate exists AND next step is being changed — direction unclear."""
    return (
        len(proposal.proposed_decision_log_candidates) > 0
        and proposal.proposed_next_expected_step_update is not None
    )


def _is_review_attention_required(
    artifact: ImplementationRunArtifact, proposal: StateUpdateProposal
) -> bool:
    """Partial run with open items, or new risks surfaced in proposal."""
    has_open_partial = (
        artifact.status == "partial" and len(artifact.unresolved_items) > 0
    )
    has_new_risks = len(proposal.proposed_risk_updates) > 0
    return has_open_partial or has_new_risks


def _evaluate_category(
    artifact: ImplementationRunArtifact, proposal: StateUpdateProposal
) -> str:
    if _is_implementation_blocked(artifact):
        return "implementation_blocked"
    if _is_state_conflict(artifact, proposal):
        return "state_conflict_detected"
    if _is_decision_required(proposal):
        return "decision_required"
    if _is_review_attention_required(artifact, proposal):
        return "review_attention_required"
    return "none"


# ---------------------------------------------------------------------------
# Evidence and message builders
# ---------------------------------------------------------------------------

_WHY_NOW = {
    "implementation_blocked": (
        "The latest run artifact indicates the implementation is not progressing. "
        "The task cannot advance without human review or a course correction."
    ),
    "state_conflict_detected": (
        "The state update proposal simultaneously suggests phase completion "
        "and surfaces new risk candidates. This tension should be resolved by the human "
        "before any state updates are applied."
    ),
    "decision_required": (
        "The proposal flags a decision candidate and a change to the next expected step. "
        "The direction forward may depend on an explicit design or architecture decision "
        "that should not be assumed."
    ),
    "review_attention_required": (
        "The run has unresolved items or new risk candidates that warrant explicit "
        "review before proceeding to the next implementation task."
    ),
    "none": "No escalation conditions were met based on current structured artifacts.",
}

_RECOMMENDED_ACTION = {
    "implementation_blocked": (
        "Review the run artifact and unresolved items. Determine whether the approach "
        "needs to change, the task needs to be decomposed differently, or a blocker "
        "requires a design decision before implementation can continue."
    ),
    "state_conflict_detected": (
        "Review the state update proposal. Decide whether the phase is truly complete "
        "or whether the new risk candidates indicate more work is needed before "
        "accepting the goal update."
    ),
    "decision_required": (
        "Review the proposed decision log candidate. Confirm or redefine the next "
        "expected step before handing back to the implementation role."
    ),
    "review_attention_required": (
        "Review the run artifact and proposal. Confirm the unresolved items are "
        "acceptable to proceed with, or direct the next implementation task accordingly."
    ),
    "none": "No human intervention required based on current state.",
}

_NOT_DECIDED = [
    "Whether the implementation approach is correct",
    "Whether the run result is acceptable to proceed",
    "Whether the state update proposal should be applied",
    "Whether the phase should be marked complete",
    "What the next implementation task should be",
]


def _build_evidence(
    artifact: ImplementationRunArtifact,
    proposal: StateUpdateProposal,
    category: str,
) -> EscalationEvidence:
    relevant_risks = proposal.proposed_risk_updates[:]

    proposal_sections: list[str] = []
    if proposal.proposed_recent_progress_additions:
        proposal_sections.append(
            f"proposed_recent_progress_additions ({len(proposal.proposed_recent_progress_additions)} items)"
        )
    if proposal.proposed_current_goal_update:
        proposal_sections.append("proposed_current_goal_update")
    if proposal.proposed_next_expected_step_update:
        proposal_sections.append("proposed_next_expected_step_update")
    if proposal.proposed_risk_updates:
        proposal_sections.append(
            f"proposed_risk_updates ({len(proposal.proposed_risk_updates)} candidates)"
        )
    if proposal.proposed_decision_log_candidates:
        proposal_sections.append(
            f"proposed_decision_log_candidates ({len(proposal.proposed_decision_log_candidates)} candidates)"
        )

    return EscalationEvidence(
        artifact_status=artifact.status,
        unresolved_items=artifact.unresolved_items,
        relevant_risks=relevant_risks,
        proposal_sections=proposal_sections,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_escalation_packet(
    state_dir: Path,
    artifact_path: Path = None,
    proposal_path: Path = None,
) -> EscalationPacket:
    """Evaluate deterministic escalation rules and generate a packet.

    If artifact_path / proposal_path are not given, the project-level defaults are used.
    Always returns a packet — category 'none' means no escalation needed.
    Does NOT modify any source-of-truth file.
    """
    reader = FileReader(state_dir)
    state = reader.read_working_state()

    if artifact_path is None:
        try:
            artifact_path = select_latest_artifact(state_dir)
        except ReviewError as e:
            raise EscalationError(str(e))

    try:
        artifact = load_artifact(artifact_path)
    except IngestionError as e:
        raise EscalationError(f"Failed to load artifact: {e}")

    if proposal_path is not None:
        if not proposal_path.exists():
            raise EscalationError(
                f"state_update_proposal.json not found at {proposal_path}. "
                "Run 'generate-state-update-proposal' first."
            )
        try:
            proposal = StateUpdateProposal(
                **json.loads(proposal_path.read_text(encoding="utf-8"))
            )
        except Exception as e:
            raise EscalationError(f"Failed to load proposal: {e}")
    else:
        proposal = load_state_update_proposal(state_dir)

    category = _evaluate_category(artifact, proposal)
    severity = CATEGORY_SEVERITY[category]
    evidence = _build_evidence(artifact, proposal, category)

    return EscalationPacket(
        generated_at=datetime.now(timezone.utc).isoformat(),
        project_name=state.project_name,
        category=category,
        severity=severity,
        why_now=_WHY_NOW[category],
        evidence=evidence,
        recommended_human_action=_RECOMMENDED_ACTION[category],
        explicitly_not_decided_by_system=_NOT_DECIDED if category != "none" else [],
    )


def save_escalation_packet(packet: EscalationPacket, state_dir: Path) -> Path:
    output_path = state_dir / "escalation_packet.json"
    output_path.write_text(
        json.dumps(packet.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
