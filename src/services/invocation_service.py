"""Phase 13 — Claude adapter stub / local invocation boundary."""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.models import ClaudeInvocation, InputFiles
from src.services.round_service import _load_round_dir, _require_round_file, RoundError


class InvocationError(Exception):
    pass


@dataclass
class PrepareInvocationResult:
    round_id: str
    round_dir: Path
    invocation_path: Path


_ADAPTER_MODE = "manual_stub"

_INPUT_TASK_FILE = "task_for_claude.md"
_INPUT_ENVELOPE = "claude_submission_envelope.json"
_INPUT_TEMPLATE = "run_artifact_template.json"
_EXPECTED_OUTPUT = "run_artifact.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_preview(project_name: str, round_id: str) -> str:
    ingest_cmd = (
        f"agent-orchestrator ingest-round-run "
        f"--project {project_name} --round {round_id} --file <path to artifact>"
    )
    lines = [
        f"Round {round_id} is ready for manual Claude submission.",
        "",
        "Inputs to hand to Claude:",
        f"  1. {_INPUT_TASK_FILE}          — human-readable task description",
        f"  2. {_INPUT_ENVELOPE}  — structured handoff context",
        f"  3. {_INPUT_TEMPLATE}   — expected return format",
        "",
        f"Expected output from Claude:  {_EXPECTED_OUTPUT}",
        "",
        "After Claude returns an artifact, ingest it with:",
        f"  {ingest_cmd}",
        "",
        "Next orchestrator step after ingestion:  review-round",
    ]
    return "\n".join(lines)


def _build_invocation(round_dir: Path, round_id: str, project_name: str) -> ClaudeInvocation:
    return ClaudeInvocation(
        project_name=project_name,
        round_id=round_id,
        adapter_mode=_ADAPTER_MODE,
        generated_at=datetime.now(timezone.utc).isoformat(),
        input_files=InputFiles(
            task_file=_INPUT_TASK_FILE,
            submission_envelope=_INPUT_ENVELOPE,
            artifact_template=_INPUT_TEMPLATE,
        ),
        expected_output_file=_EXPECTED_OUTPUT,
        invocation_preview=_build_preview(project_name, round_id),
    )


def _load_project_name(round_dir: Path) -> str:
    state_path = round_dir / "round_state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    return data["project_name"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prepare_round_invocation(
    state_dir: Path,
    round_id: str,
) -> PrepareInvocationResult:
    """Generate (or refresh) the Claude invocation descriptor for a round.

    Validates that all three submission artifacts are present:
      task_for_claude.md, claude_submission_envelope.json, run_artifact_template.json

    Writes claude_invocation.json into the round directory.
    Does NOT modify round_state.json or any source-of-truth file.
    Does NOT invoke Claude or ingest results.
    """
    round_dir = _load_round_dir(state_dir, round_id)

    try:
        _require_round_file(round_dir, _INPUT_TASK_FILE)
        _require_round_file(round_dir, _INPUT_ENVELOPE)
        _require_round_file(round_dir, _INPUT_TEMPLATE)
    except RoundError as e:
        raise InvocationError(str(e))

    project_name = _load_project_name(round_dir)
    invocation = _build_invocation(round_dir, round_id, project_name)

    invocation_path = round_dir / "claude_invocation.json"
    invocation_path.write_text(
        json.dumps(invocation.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return PrepareInvocationResult(
        round_id=round_id,
        round_dir=round_dir,
        invocation_path=invocation_path,
    )
