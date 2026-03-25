"""Tests for run artifact ingestion."""
import json
import pytest
from pathlib import Path

from src.models import ImplementationRunArtifact
from src.services.ingestion_service import (
    ingest_artifact,
    load_artifact,
    IngestionError,
    _artifact_filename,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_ARTIFACT = {
    "project_name": "cyber-community-v2",
    "generated_at": "2026-03-23T12:38:38+00:00",
    "role": "claude",
    "task_summary": "Implement Phase 26B minimal T4 activation slice.",
    "status": "partial",
    "files_changed": ["src/engine/t4_builder.py", "tests/test_t4_contract.py"],
    "implemented_items": ["Modified build_signal_from_t4_relationship_tick()"],
    "tests_run": ["test_t4_frozen_boundary", "test_contract_flip"],
    "unresolved_items": ["Contract flip test for _adjust_t4 still failing"],
    "notes": "Phase 23 gate opened as expected; _adjust_t4 chain needs one more fix.",
}


def write_artifact(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "artifact.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_artifact
# ---------------------------------------------------------------------------

class TestLoadArtifact:
    def test_valid_artifact_parses(self, tmp_path):
        p = write_artifact(tmp_path, VALID_ARTIFACT)
        artifact = load_artifact(p)
        assert isinstance(artifact, ImplementationRunArtifact)
        assert artifact.project_name == "cyber-community-v2"
        assert artifact.status == "partial"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(IngestionError, match="not found"):
            load_artifact(tmp_path / "nonexistent.json")

    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json {{", encoding="utf-8")
        with pytest.raises(IngestionError, match="not valid JSON"):
            load_artifact(p)

    def test_missing_required_field_raises(self, tmp_path):
        data = {k: v for k, v in VALID_ARTIFACT.items() if k != "task_summary"}
        p = write_artifact(tmp_path, data)
        with pytest.raises(IngestionError, match="schema invalid"):
            load_artifact(p)

    def test_invalid_status_raises(self, tmp_path):
        data = {**VALID_ARTIFACT, "status": "unknown"}
        p = write_artifact(tmp_path, data)
        with pytest.raises(IngestionError, match="schema invalid"):
            load_artifact(p)

    def test_all_valid_statuses_accepted(self, tmp_path):
        for status in ("success", "partial", "failed"):
            data = {**VALID_ARTIFACT, "status": status}
            p = write_artifact(tmp_path, data)
            artifact = load_artifact(p)
            assert artifact.status == status

    def test_optional_fields_default_to_empty(self, tmp_path):
        minimal = {
            "project_name": "proj",
            "generated_at": "2026-03-23T00:00:00+00:00",
            "role": "claude",
            "task_summary": "Do something.",
            "status": "success",
        }
        p = write_artifact(tmp_path, minimal)
        artifact = load_artifact(p)
        assert artifact.files_changed == []
        assert artifact.implemented_items == []
        assert artifact.tests_run == []
        assert artifact.unresolved_items == []
        assert artifact.notes is None


# ---------------------------------------------------------------------------
# ingest_artifact
# ---------------------------------------------------------------------------

class TestIngestArtifact:
    def test_valid_artifact_is_stored(self, tmp_path):
        artifact_file = write_artifact(tmp_path, VALID_ARTIFACT)
        state_dir = tmp_path / "projects" / "cyber-community-v2"
        state_dir.mkdir(parents=True)

        artifact, saved = ingest_artifact(artifact_file, state_dir, "cyber-community-v2")

        assert saved.exists()
        assert saved.parent.name == "artifacts"
        assert saved.suffix == ".json"

    def test_stored_content_is_valid_json(self, tmp_path):
        artifact_file = write_artifact(tmp_path, VALID_ARTIFACT)
        state_dir = tmp_path / "projects" / "cyber-community-v2"
        state_dir.mkdir(parents=True)

        _, saved = ingest_artifact(artifact_file, state_dir, "cyber-community-v2")

        data = json.loads(saved.read_text(encoding="utf-8"))
        assert data["project_name"] == "cyber-community-v2"
        assert data["status"] == "partial"

    def test_artifacts_dir_created_automatically(self, tmp_path):
        artifact_file = write_artifact(tmp_path, VALID_ARTIFACT)
        state_dir = tmp_path / "projects" / "cyber-community-v2"
        state_dir.mkdir(parents=True)

        _, saved = ingest_artifact(artifact_file, state_dir, "cyber-community-v2")

        assert (state_dir / "artifacts").is_dir()

    def test_project_mismatch_raises(self, tmp_path):
        artifact_file = write_artifact(tmp_path, VALID_ARTIFACT)
        state_dir = tmp_path / "projects" / "other-project"
        state_dir.mkdir(parents=True)

        with pytest.raises(IngestionError, match="mismatch"):
            ingest_artifact(artifact_file, state_dir, "other-project")

    def test_filename_derived_from_generated_at(self, tmp_path):
        artifact_file = write_artifact(tmp_path, VALID_ARTIFACT)
        state_dir = tmp_path / "projects" / "cyber-community-v2"
        state_dir.mkdir(parents=True)

        _, saved = ingest_artifact(artifact_file, state_dir, "cyber-community-v2")

        assert saved.name.startswith("run_")
        assert "2026-03-23" in saved.name

    def test_notes_none_excluded_from_stored_json(self, tmp_path):
        data = {k: v for k, v in VALID_ARTIFACT.items() if k != "notes"}
        artifact_file = write_artifact(tmp_path, data)
        state_dir = tmp_path / "projects" / "cyber-community-v2"
        state_dir.mkdir(parents=True)

        _, saved = ingest_artifact(artifact_file, state_dir, "cyber-community-v2")

        stored = json.loads(saved.read_text())
        assert "notes" not in stored


# ---------------------------------------------------------------------------
# _artifact_filename
# ---------------------------------------------------------------------------

class TestArtifactFilename:
    def _make(self, generated_at: str) -> ImplementationRunArtifact:
        return ImplementationRunArtifact(
            project_name="p",
            generated_at=generated_at,
            role="claude",
            task_summary="t",
            status="success",
        )

    def test_starts_with_run_prefix(self):
        artifact = self._make("2026-03-23T12:38:38+00:00")
        assert _artifact_filename(artifact).startswith("run_")

    def test_ends_with_json(self):
        artifact = self._make("2026-03-23T12:38:38+00:00")
        assert _artifact_filename(artifact).endswith(".json")

    def test_no_colons_in_filename(self):
        artifact = self._make("2026-03-23T12:38:38+00:00")
        assert ":" not in _artifact_filename(artifact)

    def test_no_plus_in_filename(self):
        artifact = self._make("2026-03-23T12:38:38+00:00")
        assert "+" not in _artifact_filename(artifact)
