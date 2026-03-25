import json
import re
from pathlib import Path

from pydantic import ValidationError

from src.models import ImplementationRunArtifact


class IngestionError(Exception):
    pass


def load_artifact(artifact_path: Path) -> ImplementationRunArtifact:
    """Parse and validate a run artifact JSON file."""
    if not artifact_path.exists():
        raise IngestionError(f"Artifact file not found: {artifact_path}")

    try:
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise IngestionError(f"Artifact is not valid JSON: {e}")

    try:
        return ImplementationRunArtifact(**data)
    except ValidationError as e:
        raise IngestionError(f"Artifact schema invalid:\n{e}")


def ingest_artifact(
    artifact_path: Path,
    state_dir: Path,
    expected_project: str,
) -> tuple[ImplementationRunArtifact, Path]:
    """Validate and store a run artifact under the project's artifacts directory.

    Returns (artifact, saved_path).
    Raises IngestionError on validation failure.
    """
    artifact = load_artifact(artifact_path)

    if artifact.project_name != expected_project:
        raise IngestionError(
            f"Project name mismatch: artifact says {artifact.project_name!r}, "
            f"expected {expected_project!r}"
        )

    artifacts_dir = state_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    filename = _artifact_filename(artifact)
    dest = artifacts_dir / filename

    dest.write_text(
        json.dumps(artifact.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return artifact, dest


def _artifact_filename(artifact: ImplementationRunArtifact) -> str:
    """Derive a deterministic filename from the artifact's generated_at timestamp."""
    # Sanitize ISO timestamp: 2026-03-23T12:38:38+00:00 -> 2026-03-23T12-38-38
    safe_ts = re.sub(r"[:\+]", "-", artifact.generated_at).split(".")[0]
    return f"run_{safe_ts}.json"
