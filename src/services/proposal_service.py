import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.models import StateUpdateProposal, ProposalBasis, ImplementationRunArtifact, ReviewPacket
from src.models.working_state import WorkingState
from .file_reader import FileReader
from .ingestion_service import load_artifact, IngestionError
from .review_service import select_latest_artifact, load_review_packet, ReviewError


class ProposalError(Exception):
    pass


# ---------------------------------------------------------------------------
# Internal derivation helpers
# ---------------------------------------------------------------------------

def _find_failing_tests(tests_run: list[str]) -> list[str]:
    """Return test entries that indicate failure."""
    return [t for t in tests_run if re.search(r"\b(FAIL|FAILED|ERROR)\b", t, re.IGNORECASE)]


def _propose_progress_additions(artifact: ImplementationRunArtifact) -> list[str]:
    """Each implemented_item becomes a candidate completed progress addition."""
    return list(artifact.implemented_items)


def _propose_next_step_update(
    artifact: ImplementationRunArtifact,
    state: WorkingState,
    review: ReviewPacket,
) -> tuple[str | None, str]:
    """Return (proposed_update, rationale).

    Priority:
    1. If unresolved_items exist → derive next step from them.
    2. If inspect_next from review differs from current next_expected_step → propose it.
    3. Otherwise → no update.
    """
    if artifact.unresolved_items:
        if len(artifact.unresolved_items) == 1:
            candidate = artifact.unresolved_items[0]
        else:
            candidate = "Resolve: " + "; ".join(artifact.unresolved_items)
        return candidate, "Derived from unresolved_items in run artifact."

    review_inspect = review.inspect_next.strip()
    current_step = state.next_expected_step.strip()
    if review_inspect and review_inspect != current_step:
        return review_inspect, "Derived from review packet inspect_next (differs from current next_expected_step)."

    return None, "Current next_expected_step still applicable; no update proposed."


def _propose_current_goal_update(
    artifact: ImplementationRunArtifact,
    state: WorkingState,
) -> tuple[str | None, str]:
    """Return (proposed_update, rationale).

    Only suggest a goal change if the run fully succeeded (status == success).
    Partial or failed runs leave the goal unchanged.
    """
    if artifact.status == "success":
        return (
            f"[Phase complete] {state.current_phase} implemented successfully. "
            "Update goal to reflect the next phase objective.",
            f"Run status is 'success' — current phase goal may now be satisfied.",
        )
    return (
        None,
        f"Run status is '{artifact.status}'; current_goal left unchanged until phase is complete.",
    )


def _propose_risk_updates(
    artifact: ImplementationRunArtifact,
    state: WorkingState,
) -> list[str]:
    """Suggest new risk entries for unresolved items and failing tests.

    Conservative: only surface what is clearly evidenced in the artifact.
    Does not modify or remove existing risks.
    """
    suggestions = []
    existing_risk_text = " ".join(r.description for r in state.current_risks).lower()

    for item in artifact.unresolved_items:
        key = item[:60].lower()
        if key not in existing_risk_text:
            suggestions.append(
                f"[NEW RISK CANDIDATE] Unresolved: {item}"
            )

    for test in _find_failing_tests(artifact.tests_run):
        key = test[:60].lower()
        if key not in existing_risk_text:
            suggestions.append(
                f"[NEW RISK CANDIDATE] Failing test: {test}"
            )

    return suggestions


def _propose_decision_log_candidates(
    artifact: ImplementationRunArtifact,
    state: WorkingState,
) -> list[str]:
    """Suggest decision log candidates only where there is clear evidence.

    Conservative: partial/failed runs with unresolved items may warrant
    documenting the resolution approach; success warrants documenting
    the implementation decision.
    """
    candidates = []

    if artifact.status == "success":
        candidates.append(
            f"Consider documenting: implementation approach for {state.current_phase} "
            f"— what was decided and why (title, decision, rationale, impact)."
        )
    elif artifact.unresolved_items:
        candidates.append(
            f"Consider documenting: resolution plan for unresolved items "
            f"from {state.current_phase} run — "
            f"what approach is chosen and why."
        )
    # Failed with no unresolved items: no candidate (insufficient basis)

    return candidates


def _build_explicitly_unchanged(
    artifact: ImplementationRunArtifact,
    state: WorkingState,
    proposed_next_step: str | None,
    proposed_goal: str | None,
    proposed_risks: list[str],
) -> list[str]:
    unchanged = ["project_charter.md — never modified by proposal generation"]

    # current_phase always stays unless explicitly approved
    unchanged.append(
        "current_phase — phase advancement requires explicit human approval"
    )

    # Pending progress items: human decides which to close
    pending = [p.item for p in state.recent_progress if not p.completed]
    if pending:
        unchanged.append(
            f"Existing pending progress items ({len(pending)}) — "
            "completion status requires human review: "
            + "; ".join(f'"{item}"' for item in pending)
        )

    # existing risks if no risk proposals
    if not proposed_risks:
        unchanged.append("current_risks — no new risk evidence found in this run")

    if proposed_next_step is None:
        unchanged.append("next_expected_step — current value still applicable")

    if proposed_goal is None:
        unchanged.append(
            f"current_goal — run status is '{artifact.status}', goal remains in progress"
        )

    return unchanged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_state_update_proposal(
    state_dir: Path,
    artifact_path: Path = None,
    review_packet_path: Path = None,
) -> StateUpdateProposal:
    """Generate a conservative, deterministic state update proposal.

    Reads: source-of-truth files, a run artifact, a review packet.
    If artifact_path / review_packet_path are not given, the project-level defaults are used.
    Does NOT modify any source-of-truth file.
    """
    reader = FileReader(state_dir)
    state = reader.read_working_state()

    if artifact_path is None:
        try:
            artifact_path = select_latest_artifact(state_dir)
        except ReviewError as e:
            raise ProposalError(str(e))

    try:
        artifact = load_artifact(artifact_path)
    except IngestionError as e:
        raise ProposalError(f"Failed to load artifact: {e}")

    if review_packet_path is None:
        review_packet_path = state_dir / "review_packet.json"

    if not review_packet_path.exists():
        raise ProposalError(
            f"review_packet.json not found at {review_packet_path}. "
            "Run 'generate-review-packet' first."
        )
    try:
        review = ReviewPacket(**json.loads(review_packet_path.read_text(encoding="utf-8")))
    except Exception as e:
        raise ProposalError(f"Failed to load review packet: {e}")

    # Derive each proposal section
    progress_additions = _propose_progress_additions(artifact)

    proposed_next_step, next_step_rationale = _propose_next_step_update(artifact, state, review)
    proposed_goal, goal_rationale = _propose_current_goal_update(artifact, state)
    proposed_risks = _propose_risk_updates(artifact, state)
    proposed_decisions = _propose_decision_log_candidates(artifact, state)

    explicitly_unchanged = _build_explicitly_unchanged(
        artifact, state, proposed_next_step, proposed_goal, proposed_risks
    )

    rationale_notes = [
        f"proposed_recent_progress_additions: {len(progress_additions)} item(s) from artifact.implemented_items.",
        f"proposed_next_expected_step_update: {next_step_rationale}",
        f"proposed_current_goal_update: {goal_rationale}",
        f"proposed_risk_updates: {len(proposed_risks)} candidate(s) surfaced from unresolved items and failing tests.",
        f"proposed_decision_log_candidates: {len(proposed_decisions)} candidate(s) based on run status.",
        "proposed_recent_progress_updates: left empty — existing pending item completion requires human judgement.",
    ]

    return StateUpdateProposal(
        generated_at=datetime.now(timezone.utc).isoformat(),
        project_name=state.project_name,
        based_on=ProposalBasis(
            artifact_path=str(artifact_path),
            review_packet_path=str(review_packet_path),
        ),
        proposed_recent_progress_additions=progress_additions,
        proposed_recent_progress_updates=[],
        proposed_current_goal_update=proposed_goal,
        proposed_next_expected_step_update=proposed_next_step,
        proposed_risk_updates=proposed_risks,
        proposed_decision_log_candidates=proposed_decisions,
        explicitly_unchanged=explicitly_unchanged,
        rationale_notes=rationale_notes,
    )


def save_state_update_proposal(proposal: StateUpdateProposal, state_dir: Path) -> Path:
    output_path = state_dir / "state_update_proposal.json"
    output_path.write_text(
        json.dumps(proposal.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
