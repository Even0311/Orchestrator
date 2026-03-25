"""Tests for Phase 14 — run artifact contract validation."""
import json
from pathlib import Path

import pytest

from src.services.validation_service import validate_run_artifact, ArtifactValidationResult

VALID_ARTIFACT = {
    "project_name": "test-project",
    "generated_at": "2026-03-25T10:00:00Z",
    "role": "claude",
    "task_summary": "Implemented feature X.",
    "status": "success",
    "files_changed": ["src/feature_x.py"],
    "implemented_items": ["Added feature_x()"],
    "tests_run": ["test_feature_x — PASS"],
    "unresolved_items": [],
}


def write_artifact(tmp_path: Path, data) -> Path:
    p = tmp_path / "artifact.json"
    if isinstance(data, dict):
        p.write_text(json.dumps(data), encoding="utf-8")
    else:
        p.write_text(data, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Valid artifact
# ---------------------------------------------------------------------------

class TestValidArtifact:
    def test_valid_artifact_passes(self, tmp_path):
        p = write_artifact(tmp_path, VALID_ARTIFACT)
        result = validate_run_artifact(p)
        assert result.valid is True
        assert result.errors == []

    def test_partial_status_passes(self, tmp_path):
        data = {**VALID_ARTIFACT, "status": "partial", "unresolved_items": ["item"]}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is True

    def test_failed_status_passes(self, tmp_path):
        data = {**VALID_ARTIFACT, "status": "failed"}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is True

    def test_empty_lists_pass(self, tmp_path):
        data = {**VALID_ARTIFACT, "files_changed": [], "implemented_items": [],
                "tests_run": [], "unresolved_items": []}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is True

    def test_extra_notes_field_passes(self, tmp_path):
        data = {**VALID_ARTIFACT, "notes": "Some note."}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is True


# ---------------------------------------------------------------------------
# File / JSON errors
# ---------------------------------------------------------------------------

class TestFileErrors:
    def test_missing_file_returns_error(self, tmp_path):
        result = validate_run_artifact(tmp_path / "nonexistent.json")
        assert result.valid is False
        assert any("not found" in e.lower() or "file" in e.lower() for e in result.errors)

    def test_invalid_json_returns_error(self, tmp_path):
        p = write_artifact(tmp_path, "{ not valid json }")
        result = validate_run_artifact(p)
        assert result.valid is False
        assert any("json" in e.lower() or "invalid" in e.lower() for e in result.errors)

    def test_json_array_top_level_returns_error(self, tmp_path):
        p = write_artifact(tmp_path, "[1, 2, 3]")
        result = validate_run_artifact(p)
        assert result.valid is False
        assert any("object" in e.lower() for e in result.errors)

    def test_multiline_string_in_json_value_returns_error(self, tmp_path):
        # Raw string with a literal newline inside a JSON string value
        raw = '{"project_name": "test",\n"task_summary": "line1\nline2",\n"generated_at": "2026-03-25T10:00:00Z","role":"claude","status":"success","files_changed":[],"implemented_items":[],"tests_run":[],"unresolved_items":[]}'
        p = tmp_path / "artifact.json"
        p.write_bytes(raw.encode("utf-8"))
        result = validate_run_artifact(p)
        assert result.valid is False


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------

class TestMissingFields:
    @pytest.mark.parametrize("field", [
        "project_name", "generated_at", "role", "task_summary",
        "status", "files_changed", "implemented_items", "tests_run", "unresolved_items",
    ])
    def test_missing_field_returns_error(self, tmp_path, field):
        data = {k: v for k, v in VALID_ARTIFACT.items() if k != field}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is False
        assert any(field in e for e in result.errors)


# ---------------------------------------------------------------------------
# Invalid field values
# ---------------------------------------------------------------------------

class TestInvalidValues:
    def test_invalid_status_returns_error(self, tmp_path):
        data = {**VALID_ARTIFACT, "status": "done"}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is False
        assert any("status" in e for e in result.errors)

    def test_list_field_as_string_returns_error(self, tmp_path):
        data = {**VALID_ARTIFACT, "files_changed": "src/foo.py"}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is False
        assert any("files_changed" in e for e in result.errors)

    def test_list_field_as_dict_returns_error(self, tmp_path):
        data = {**VALID_ARTIFACT, "unresolved_items": {"a": 1}}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert result.valid is False


# ---------------------------------------------------------------------------
# Template placeholder warnings
# ---------------------------------------------------------------------------

class TestTemplateWarnings:
    def test_unfilled_placeholder_produces_warning(self, tmp_path):
        data = {**VALID_ARTIFACT, "task_summary": "FILL: one-line summary"}
        result = validate_run_artifact(write_artifact(tmp_path, data))
        assert any("task_summary" in w for w in result.warnings)

    def test_filled_artifact_has_no_warnings(self, tmp_path):
        result = validate_run_artifact(write_artifact(tmp_path, VALID_ARTIFACT))
        assert result.warnings == []


# ---------------------------------------------------------------------------
# Template contract (from submission_service)
# ---------------------------------------------------------------------------

class TestTemplateContract:
    def test_template_has_all_required_fields(self, tmp_path):
        from src.services.submission_service import _build_template
        template = _build_template("test-project")
        required = [
            "project_name", "generated_at", "role", "task_summary",
            "status", "files_changed", "implemented_items", "tests_run", "unresolved_items",
        ]
        for field in required:
            assert field in template, f"Template missing field: {field}"

    def test_template_project_name_is_real(self, tmp_path):
        from src.services.submission_service import _build_template
        t = _build_template("my-project")
        assert t["project_name"] == "my-project"

    def test_template_role_is_claude(self, tmp_path):
        from src.services.submission_service import _build_template
        assert _build_template("x")["role"] == "claude"

    def test_template_unresolved_items_is_empty_list(self, tmp_path):
        from src.services.submission_service import _build_template
        assert _build_template("x")["unresolved_items"] == []


# ---------------------------------------------------------------------------
# Task file references contract clearly
# ---------------------------------------------------------------------------

class TestTaskFileContract:
    def _task_file_content(self, tmp_path) -> str:
        from src.services.round_service import start_round
        state_dir = tmp_path / "projects" / "test-project"
        state_dir.mkdir(parents=True)
        (state_dir / "working_state.yaml").write_text(
            "project_name: test-project\ncurrent_phase: Phase 1\n"
            "current_goal: Do something.\nnext_expected_step: Run tests.\n"
            "recent_progress: []\ncurrent_risks: []\n",
            encoding="utf-8",
        )
        (state_dir / "decision_log.yaml").write_text("decisions: []\n", encoding="utf-8")
        (state_dir / "project_charter.md").write_text(
            "# Charter\n\n## 项目概述\nOverview.\n", encoding="utf-8"
        )
        r = start_round(state_dir)
        return r.task_file_path.read_text(encoding="utf-8")

    def test_task_file_references_template(self, tmp_path):
        content = self._task_file_content(tmp_path)
        assert "run_artifact_template.json" in content

    def test_task_file_mentions_no_line_breaks_rule(self, tmp_path):
        content = self._task_file_content(tmp_path)
        assert "line" in content.lower()

    def test_task_file_mentions_json_only_rule(self, tmp_path):
        content = self._task_file_content(tmp_path)
        assert "json" in content.lower()
