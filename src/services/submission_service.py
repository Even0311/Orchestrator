"""Phase 12 — Claude runner interface / submission envelope service."""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.models import TaskPacket, ClaudeSubmissionEnvelope, Deliverables, RoundFiles
from src.services.round_service import _load_round_dir, _require_round_file, RoundError


class SubmissionError(Exception):
    pass


@dataclass
class PrepareSubmissionResult:
    round_id: str
    round_dir: Path
    envelope_path: Path
    template_path: Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_task_packet(round_dir: Path) -> TaskPacket:
    packet_path = _require_round_file(round_dir, "task_packet_claude.json")
    return TaskPacket(**json.loads(packet_path.read_text(encoding="utf-8")))


def _build_envelope(packet: TaskPacket, round_id: str) -> ClaudeSubmissionEnvelope:
    ingest_cmd = (
        f"agent-orchestrator ingest-round-run "
        f"--project {packet.project_name} --round {round_id} --file <path>"
    )
    return ClaudeSubmissionEnvelope(
        project_name=packet.project_name,
        round_id=round_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        current_phase=packet.current_phase,
        current_goal=packet.current_goal,
        next_expected_step=packet.next_expected_step,
        implementation_boundaries=packet.implementation_boundaries,
        current_risks=packet.current_risks,
        deliverables=Deliverables(
            description=(
                "Return a structured JSON artifact matching run_artifact_template.json "
                "in this round directory."
            ),
            ingest_command=ingest_cmd,
        ),
        round_files=RoundFiles(),
    )


def _build_template(project_name: str) -> dict:
    return {
        "_instructions": (
            "Fill every FILL: value. Remove this _instructions field before submitting. "
            "All string values must be on a single line — no line breaks inside strings. "
            "status must be exactly: success, partial, or failed."
        ),
        "project_name": project_name,
        "generated_at": "FILL: ISO timestamp e.g. 2026-03-25T10:00:00Z",
        "role": "claude",
        "task_summary": "FILL: one-line summary of what you did — no line breaks",
        "status": "FILL: success | partial | failed",
        "files_changed": ["FILL: path/to/changed_file.py"],
        "implemented_items": ["FILL: completed item, one per entry"],
        "tests_run": ["FILL: test_name — PASS or FAIL"],
        "unresolved_items": [],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prepare_round_submission(
    state_dir: Path,
    round_id: str,
) -> PrepareSubmissionResult:
    """Generate (or refresh) the Claude submission envelope and run artifact template.

    Requires task_packet_claude.json in the round directory (written by start_round).
    Writes claude_submission_envelope.json and run_artifact_template.json.
    Does NOT modify source-of-truth files or round_state.json.
    """
    round_dir = _load_round_dir(state_dir, round_id)

    try:
        packet = _load_task_packet(round_dir)
    except RoundError as e:
        raise SubmissionError(str(e))

    envelope = _build_envelope(packet, round_id)
    envelope_path = round_dir / "claude_submission_envelope.json"
    envelope_path.write_text(
        json.dumps(envelope.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    template = _build_template(packet.project_name)
    template_path = round_dir / "run_artifact_template.json"
    template_path.write_text(
        json.dumps(template, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return PrepareSubmissionResult(
        round_id=round_id,
        round_dir=round_dir,
        envelope_path=envelope_path,
        template_path=template_path,
    )
