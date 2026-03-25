import json
from datetime import datetime, timezone
from pathlib import Path

from src.models import ReviewPacket, RunSummary, ImplementationRunArtifact
from .file_reader import FileReader
from .ingestion_service import load_artifact, IngestionError


RECENT_DECISIONS_LIMIT = 5


class ReviewError(Exception):
    pass


def select_latest_artifact(state_dir: Path) -> Path:
    """Return the most recently generated artifact from the artifacts directory.

    Selection rule: lexicographic max of run_*.json filenames.
    Filenames are ISO-timestamp-derived (run_YYYY-MM-DDTHH-MM-SS...) so
    lexicographic order equals chronological order.
    """
    artifacts_dir = state_dir / "artifacts"
    if not artifacts_dir.exists():
        raise ReviewError(
            f"No artifacts directory found under {state_dir}. "
            "Run 'ingest-run' first."
        )
    candidates = sorted(artifacts_dir.glob("run_*.json"))
    if not candidates:
        raise ReviewError(
            f"No run artifacts found in {artifacts_dir}. "
            "Run 'ingest-run' first."
        )
    return candidates[-1]


def _derive_inspect_next(artifact: ImplementationRunArtifact, next_expected_step: str) -> str:
    """Derive inspect_next deterministically.

    If unresolved_items are present, list them (they represent what failed or
    remains open from the run).  Otherwise fall back to next_expected_step
    from the project source of truth.
    """
    if artifact.unresolved_items:
        if len(artifact.unresolved_items) == 1:
            return artifact.unresolved_items[0]
        items = "\n".join(f"- {item}" for item in artifact.unresolved_items)
        return f"Unresolved items from run:\n{items}"
    return next_expected_step.strip()


def generate_review_packet(state_dir: Path, artifact_path: Path = None) -> ReviewPacket:
    """Generate a review packet from project source-of-truth and a run artifact.

    If artifact_path is not given, the latest artifact is selected automatically.
    """
    reader = FileReader(state_dir)
    charter = reader.read_charter()
    state = reader.read_working_state()
    log = reader.read_decision_log()

    if artifact_path is None:
        artifact_path = select_latest_artifact(state_dir)

    try:
        artifact = load_artifact(artifact_path)
    except IngestionError as e:
        raise ReviewError(f"Failed to load artifact: {e}")

    # Validate against directory name (same convention as ingestion).
    # working_state.project_name may be a display name and differ from the dir name.
    dir_name = state_dir.name
    if artifact.project_name != dir_name:
        raise ReviewError(
            f"Artifact project_name {artifact.project_name!r} does not match "
            f"project directory {dir_name!r}"
        )

    run_summary = RunSummary(
        task_summary=artifact.task_summary,
        status=artifact.status,
        files_changed=artifact.files_changed,
        implemented_items=artifact.implemented_items,
        tests_run=artifact.tests_run,
        unresolved_items=artifact.unresolved_items,
        notes=artifact.notes,
    )

    inspect_next = _derive_inspect_next(artifact, state.next_expected_step)

    return ReviewPacket(
        generated_at=datetime.now(timezone.utc).isoformat(),
        project_name=state.project_name,
        current_phase=state.current_phase,
        current_goal=state.current_goal.strip(),
        project_summary=reader.build_charter_summary(charter),
        recent_progress=state.recent_progress,
        current_risks=state.current_risks,
        recent_decisions=log.decisions[-RECENT_DECISIONS_LIMIT:],
        run_summary=run_summary,
        inspect_next=inspect_next,
    )


def load_review_packet(state_dir: Path) -> ReviewPacket:
    """Load the current review packet for a project."""
    path = state_dir / "review_packet.json"
    if not path.exists():
        raise ReviewError(
            f"review_packet.json not found in {state_dir}. "
            "Run 'generate-review-packet' first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return ReviewPacket(**data)


def save_review_packet(packet: ReviewPacket, state_dir: Path) -> Path:
    output_path = state_dir / "review_packet.json"
    output_path.write_text(
        json.dumps(packet.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
