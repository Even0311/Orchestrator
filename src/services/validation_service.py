"""Phase 14 — Run artifact contract validation."""
import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from src.models import ImplementationRunArtifact


_REQUIRED_FIELDS = [
    "project_name",
    "generated_at",
    "role",
    "task_summary",
    "status",
    "files_changed",
    "implemented_items",
    "tests_run",
    "unresolved_items",
]

_LIST_FIELDS = ["files_changed", "implemented_items", "tests_run", "unresolved_items"]
_VALID_STATUSES = {"success", "partial", "failed"}


@dataclass
class ArtifactValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_run_artifact(artifact_path: Path) -> ArtifactValidationResult:
    """Validate a run artifact file against the ImplementationRunArtifact contract.

    Returns an ArtifactValidationResult with specific, actionable error messages.
    Does not modify any files.
    """
    if not artifact_path.exists():
        return ArtifactValidationResult(
            valid=False,
            errors=[f"File not found: {artifact_path}"],
        )

    # Step 1: parse JSON
    try:
        text = artifact_path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return ArtifactValidationResult(
            valid=False,
            errors=[f"Invalid JSON — {e}"],
        )

    # Step 2: top-level must be an object
    if not isinstance(data, dict):
        return ArtifactValidationResult(
            valid=False,
            errors=[f"Top-level value must be a JSON object, got {type(data).__name__}."],
        )

    errors: list[str] = []
    warnings: list[str] = []

    # Step 3: required fields
    for f in _REQUIRED_FIELDS:
        if f not in data:
            errors.append(f"Missing required field: '{f}'")

    if errors:
        return ArtifactValidationResult(valid=False, errors=errors)

    # Step 4: status enum
    if data["status"] not in _VALID_STATUSES:
        errors.append(
            f"'status' must be one of: success, partial, failed — got {data['status']!r}"
        )

    # Step 5: list fields
    for lf in _LIST_FIELDS:
        if not isinstance(data[lf], list):
            errors.append(
                f"'{lf}' must be a JSON array, got {type(data[lf]).__name__}"
            )

    # Step 6: warn on unfilled template placeholders
    for key, value in data.items():
        if isinstance(value, str) and value.startswith("FILL:"):
            warnings.append(
                f"Field '{key}' still contains a template placeholder: {value!r}"
            )

    if errors:
        return ArtifactValidationResult(valid=False, errors=errors, warnings=warnings)

    # Step 7: pydantic model validation (catches type coercion issues, pattern checks)
    try:
        ImplementationRunArtifact(**data)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            errors.append(f"Schema error at '{loc}': {err['msg']}")

    return ArtifactValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
