"""Phase 8–11 — Round workspace / round state service."""
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.models import RoundState, TaskPacket, ReviewPacket, StateUpdateProposal, EscalationPacket
from src.services.file_reader import FileReader
from src.services.task_packet_service import generate_task_packet
from src.services.ingestion_service import load_artifact, IngestionError
from src.services.review_service import generate_review_packet, ReviewError
from src.services.proposal_service import generate_state_update_proposal, ProposalError
from src.services.escalation_service import generate_escalation_packet, EscalationError
from src.services.apply_service import apply_approved_update, ApplyError, ApplyResult


class RoundError(Exception):
    pass


@dataclass
class RoundStartResult:
    round_id: str
    round_dir: Path
    round_state_path: Path
    task_packet_path: Path
    task_file_path: Path


@dataclass
class RoundIngestResult:
    round_id: str
    artifact_path: Path
    previously_had_artifact: bool


# ---------------------------------------------------------------------------
# Shared round directory helpers
# ---------------------------------------------------------------------------

def _load_round_dir(state_dir: Path, round_id: str) -> Path:
    round_dir = state_dir / "rounds" / round_id
    if not round_dir.is_dir():
        raise RoundError(
            f"Round '{round_id}' does not exist under {state_dir / 'rounds'}."
        )
    return round_dir


def _require_round_file(round_dir: Path, filename: str) -> Path:
    path = round_dir / filename
    if not path.exists():
        raise RoundError(
            f"Required file '{filename}' not found in round {round_dir.name}. "
            "Run the prerequisite step first."
        )
    return path


def _save_packet(packet, dest: Path) -> None:
    dest.write_text(
        json.dumps(packet.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _update_round_state(round_dir: Path, **updates) -> RoundState:
    """Load round_state.json, apply field updates, stamp updated_at, write back."""
    state_path = round_dir / "round_state.json"
    state = RoundState(**json.loads(state_path.read_text(encoding="utf-8")))
    for key, value in updates.items():
        setattr(state, key, value)
    state.updated_at = datetime.now(timezone.utc).isoformat()
    state_path.write_text(
        json.dumps(state.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return state


# ---------------------------------------------------------------------------
# Round ID
# ---------------------------------------------------------------------------

def _next_round_id(rounds_dir: Path) -> str:
    """Return the next monotonic round id (round-0001, round-0002, …)."""
    if not rounds_dir.exists():
        return "round-0001"
    nums = [
        int(m.group(1))
        for d in rounds_dir.iterdir()
        if d.is_dir() and (m := re.match(r"^round-(\d{4,})$", d.name))
    ]
    return f"round-{max(nums) + 1:04d}" if nums else "round-0001"


# ---------------------------------------------------------------------------
# Claude task file renderer
# ---------------------------------------------------------------------------

def _render_task_file(packet: TaskPacket, round_id: str) -> str:
    """Render a human-readable markdown task file suitable for handing to Claude."""
    lines: list[str] = [
        f"# Task — {packet.project_name}",
        "",
        f"**Round:** {round_id}",
        f"**Phase:** {packet.current_phase}",
        f"**Goal:** {packet.current_goal}",
        "",
        "## Next Expected Step",
        "",
        packet.next_expected_step or "(not specified)",
        "",
    ]

    if packet.implementation_boundaries:
        lines += ["## Implementation Boundaries", ""]
        for b in packet.implementation_boundaries:
            lines.append(f"- {b}")
        lines.append("")

    if packet.current_risks:
        lines += ["## Current Risks", ""]
        for r in packet.current_risks:
            lines.append(f"- [{r.severity.upper()}] {r.description}")
        lines.append("")

    lines += [
        "## Return Contract",
        "",
        "After completing your work, return a run artifact as a JSON object.",
        "A pre-filled template is provided in this round directory: `run_artifact_template.json`.",
        "",
        "**Rules — read carefully:**",
        "",
        f"- `project_name` must be exactly `{packet.project_name}`",
        "- `status` must be exactly `success`, `partial`, or `failed`",
        "- `unresolved_items` must be present — use `[]` if none",
        "- Every string value must be on a **single line** — no line breaks inside strings",
        "- Remove the `_instructions` field from the template before submitting",
        "- Return **only** the JSON object — do not mix prose into the artifact",
        "",
        "Paste the completed JSON in a fenced `json` block at the end of your response:",
        "",
        "```json",
        "{",
        f'  "project_name": "{packet.project_name}",',
        '  "generated_at": "2026-03-25T10:00:00Z",',
        '  "role": "claude",',
        '  "task_summary": "One-line summary.",',
        '  "status": "success",',
        '  "files_changed": ["path/to/file.py"],',
        '  "implemented_items": ["Item 1", "Item 2"],',
        '  "tests_run": ["test_foo — PASS"],',
        '  "unresolved_items": []',
        "}",
        "```",
    ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_round(state_dir: Path) -> RoundStartResult:
    """Create a new round workspace for the given project.

    Reads source-of-truth files, generates a claude task packet, creates a
    round directory, and writes round_state.json, task_packet_claude.json,
    and task_for_claude.md.

    Does NOT modify working_state.yaml, decision_log.yaml, or project_charter.md.
    """
    reader = FileReader(state_dir)
    state = reader.read_working_state()

    try:
        packet = generate_task_packet(state_dir, "claude")
    except Exception as e:
        raise RoundError(f"Failed to generate claude task packet: {e}")

    rounds_dir = state_dir / "rounds"
    round_id = _next_round_id(rounds_dir)
    round_dir = rounds_dir / round_id
    round_dir.mkdir(parents=True)

    round_state = RoundState(
        round_id=round_id,
        project_name=state.project_name,
        created_at=datetime.now(timezone.utc).isoformat(),
        status="task_ready",
        source_task_role="claude",
        based_on_phase=state.current_phase,
        based_on_goal=state.current_goal.strip(),
    )

    round_state_path = round_dir / "round_state.json"
    round_state_path.write_text(
        json.dumps(round_state.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    task_packet_path = round_dir / "task_packet_claude.json"
    task_packet_path.write_text(
        json.dumps(packet.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    task_file_path = round_dir / "task_for_claude.md"
    task_file_path.write_text(_render_task_file(packet, round_id), encoding="utf-8")

    return RoundStartResult(
        round_id=round_id,
        round_dir=round_dir,
        round_state_path=round_state_path,
        task_packet_path=task_packet_path,
        task_file_path=task_file_path,
    )


# ---------------------------------------------------------------------------
# Phase 9 — round-scoped run ingestion
# ---------------------------------------------------------------------------

def ingest_round_run(
    state_dir: Path,
    round_id: str,
    artifact_path: Path,
    expected_project: str,
) -> RoundIngestResult:
    """Attach a run artifact to an existing round.

    Validates artifact schema and project name, stores a round-local copy at
    run_artifact.json, and updates round_state.json minimally.

    Repeated ingestion overwrites the existing run_artifact.json (last write wins).
    Does NOT modify working_state.yaml, decision_log.yaml, or project_charter.md.
    """
    round_dir = _load_round_dir(state_dir, round_id)

    try:
        artifact = load_artifact(artifact_path)
    except IngestionError as e:
        raise RoundError(str(e))

    if artifact.project_name != expected_project:
        raise RoundError(
            f"Project name mismatch: artifact says {artifact.project_name!r}, "
            f"expected {expected_project!r}."
        )

    dest = round_dir / "run_artifact.json"
    previously_had = dest.exists()
    dest.write_text(
        json.dumps(artifact.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    _update_round_state(
        round_dir,
        status="run_received",
        has_run_artifact=True,
        latest_run_artifact=dest.name,
    )

    return RoundIngestResult(
        round_id=round_id,
        artifact_path=dest,
        previously_had_artifact=previously_had,
    )


# ---------------------------------------------------------------------------
# Phase 10 — round-scoped review / proposal / escalation generation
# ---------------------------------------------------------------------------

def generate_round_review(state_dir: Path, round_id: str) -> tuple[ReviewPacket, Path]:
    """Generate a review packet scoped to a round.

    Requires run_artifact.json in the round directory.
    Writes review_packet.json into the round directory.
    Does NOT modify source-of-truth files.
    """
    round_dir = _load_round_dir(state_dir, round_id)
    artifact_path = _require_round_file(round_dir, "run_artifact.json")

    try:
        packet = generate_review_packet(state_dir, artifact_path=artifact_path)
    except ReviewError as e:
        raise RoundError(str(e))

    saved = round_dir / "review_packet.json"
    _save_packet(packet, saved)
    _update_round_state(round_dir, status="review_ready", has_review_packet=True)
    return packet, saved


def generate_round_proposal(state_dir: Path, round_id: str) -> tuple[StateUpdateProposal, Path]:
    """Generate a state update proposal scoped to a round.

    Requires run_artifact.json and review_packet.json in the round directory.
    Writes state_update_proposal.json into the round directory.
    Does NOT modify source-of-truth files.
    """
    round_dir = _load_round_dir(state_dir, round_id)
    artifact_path = _require_round_file(round_dir, "run_artifact.json")
    review_packet_path = _require_round_file(round_dir, "review_packet.json")

    try:
        proposal = generate_state_update_proposal(
            state_dir,
            artifact_path=artifact_path,
            review_packet_path=review_packet_path,
        )
    except ProposalError as e:
        raise RoundError(str(e))

    saved = round_dir / "state_update_proposal.json"
    _save_packet(proposal, saved)
    _update_round_state(round_dir, status="proposal_ready", has_proposal=True)
    return proposal, saved


def generate_round_escalation(state_dir: Path, round_id: str) -> tuple[EscalationPacket, Path]:
    """Generate an escalation packet scoped to a round.

    Requires run_artifact.json and state_update_proposal.json in the round directory.
    Writes escalation_packet.json into the round directory.
    Does NOT modify source-of-truth files.
    """
    round_dir = _load_round_dir(state_dir, round_id)
    artifact_path = _require_round_file(round_dir, "run_artifact.json")
    proposal_path = _require_round_file(round_dir, "state_update_proposal.json")

    try:
        packet = generate_escalation_packet(
            state_dir,
            artifact_path=artifact_path,
            proposal_path=proposal_path,
        )
    except EscalationError as e:
        raise RoundError(str(e))

    saved = round_dir / "escalation_packet.json"
    _save_packet(packet, saved)
    new_status = "escalation_ready" if packet.category != "none" else "proposal_ready"
    _update_round_state(
        round_dir,
        status=new_status,
        has_escalation=True,
        escalation_category=packet.category,
    )
    return packet, saved


# ---------------------------------------------------------------------------
# Phase 11 — round progression: close and inspect
# ---------------------------------------------------------------------------

def close_round(state_dir: Path, round_id: str) -> ApplyResult:
    """Apply the round's approved proposal and mark the round as closed.

    Requires state_update_proposal.json in the round directory.
    Calls apply_approved_update and then sets round status to 'closed'.
    Raises ApplyError if the proposal cannot be applied.
    """
    round_dir = _load_round_dir(state_dir, round_id)
    proposal_path = _require_round_file(round_dir, "state_update_proposal.json")
    result = apply_approved_update(state_dir, proposal_path)
    _update_round_state(round_dir, status="closed")
    return result


def get_round_state(state_dir: Path, round_id: str) -> RoundState:
    """Load and return the current round state."""
    round_dir = _load_round_dir(state_dir, round_id)
    return RoundState(**json.loads(
        (round_dir / "round_state.json").read_text(encoding="utf-8")
    ))
