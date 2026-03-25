"""Tests for Phase 9 round run attachment / round-scoped ingestion."""
import json
from pathlib import Path

import pytest

from src.services.round_service import start_round, ingest_round_run, RoundError
from src.models import RoundState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WORKING_STATE_YAML = """\
project_name: test-project
current_phase: Phase 10
current_goal: Implement feature Y.
next_expected_step: Run integration tests.
recent_progress:
  - item: Task A
    completed: true
current_risks:
  - description: Known risk
    severity: medium
"""

ARTIFACT_BASE = {
    "project_name": "test-project",
    "generated_at": "2026-03-24T10:00:00+00:00",
    "role": "claude",
    "task_summary": "Implement feature Y.",
    "status": "partial",
    "files_changed": ["src/feature_y.py"],
    "implemented_items": ["Added feature_y()"],
    "tests_run": ["test_basic — PASS", "test_edge — FAIL"],
    "unresolved_items": ["test_edge failing"],
}


def setup_project(tmp_path: Path) -> Path:
    state_dir = tmp_path / "projects" / "test-project"
    state_dir.mkdir(parents=True)
    (state_dir / "working_state.yaml").write_text(WORKING_STATE_YAML, encoding="utf-8")
    (state_dir / "decision_log.yaml").write_text("decisions: []\n", encoding="utf-8")
    (state_dir / "project_charter.md").write_text(
        "# Charter\n\n## 项目概述\nOverview.\n", encoding="utf-8"
    )
    return state_dir


def write_artifact(tmp_path: Path, data: dict = None) -> Path:
    data = data or ARTIFACT_BASE
    p = tmp_path / "artifact.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Valid ingestion
# ---------------------------------------------------------------------------

class TestValidIngestion:
    def test_run_artifact_written_to_round_dir(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        artifact_path = write_artifact(tmp_path)
        result = ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")
        assert result.artifact_path.exists()
        assert result.artifact_path.name == "run_artifact.json"
        assert result.artifact_path.parent == r.round_dir

    def test_stored_artifact_is_valid_json(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        artifact_path = write_artifact(tmp_path)
        result = ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")
        data = json.loads(result.artifact_path.read_text())
        assert data["project_name"] == "test-project"
        assert data["status"] == "partial"

    def test_previously_had_artifact_false_on_first_ingest(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        artifact_path = write_artifact(tmp_path)
        result = ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")
        assert result.previously_had_artifact is False

    def test_round_id_in_result(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        artifact_path = write_artifact(tmp_path)
        result = ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")
        assert result.round_id == r.round_id


# ---------------------------------------------------------------------------
# Round state update
# ---------------------------------------------------------------------------

class TestRoundStateUpdate:
    def _load_state(self, round_dir: Path) -> RoundState:
        return RoundState(**json.loads((round_dir / "round_state.json").read_text()))

    def test_status_becomes_run_received(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        state = self._load_state(r.round_dir)
        assert state.status == "run_received"

    def test_has_run_artifact_becomes_true(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        state = self._load_state(r.round_dir)
        assert state.has_run_artifact is True

    def test_latest_run_artifact_field_set(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        state = self._load_state(r.round_dir)
        assert state.latest_run_artifact == "run_artifact.json"

    def test_updated_at_field_populated(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        state = self._load_state(r.round_dir)
        assert state.updated_at is not None

    def test_other_round_state_fields_preserved(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        state = self._load_state(r.round_dir)
        assert state.round_id == r.round_id
        assert state.based_on_phase == "Phase 10"
        assert state.source_task_role == "claude"


# ---------------------------------------------------------------------------
# Repeated ingestion
# ---------------------------------------------------------------------------

class TestRepeatedIngestion:
    def test_repeated_ingestion_overwrites(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        artifact_path = write_artifact(tmp_path)
        ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")

        updated_artifact = tmp_path / "artifact_v2.json"
        updated_artifact.write_text(
            json.dumps({**ARTIFACT_BASE, "status": "success", "unresolved_items": []}),
            encoding="utf-8",
        )
        result2 = ingest_round_run(state_dir, r.round_id, updated_artifact, "test-project")

        data = json.loads(result2.artifact_path.read_text())
        assert data["status"] == "success"

    def test_previously_had_artifact_true_on_repeat(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        artifact_path = write_artifact(tmp_path)
        ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")
        result2 = ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")
        assert result2.previously_had_artifact is True


# ---------------------------------------------------------------------------
# Validation failures
# ---------------------------------------------------------------------------

class TestValidationFailures:
    def test_missing_round_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        artifact_path = write_artifact(tmp_path)
        with pytest.raises(RoundError, match="does not exist"):
            ingest_round_run(state_dir, "round-0099", artifact_path, "test-project")

    def test_missing_artifact_file_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        with pytest.raises(RoundError, match="not found"):
            ingest_round_run(state_dir, r.round_id, tmp_path / "ghost.json", "test-project")

    def test_invalid_artifact_json_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(RoundError):
            ingest_round_run(state_dir, r.round_id, bad, "test-project")

    def test_invalid_artifact_schema_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"project_name": "test-project"}), encoding="utf-8")
        with pytest.raises(RoundError):
            ingest_round_run(state_dir, r.round_id, bad, "test-project")

    def test_project_mismatch_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        artifact_path = write_artifact(tmp_path, {**ARTIFACT_BASE, "project_name": "other-project"})
        with pytest.raises(RoundError, match="mismatch"):
            ingest_round_run(state_dir, r.round_id, artifact_path, "test-project")


# ---------------------------------------------------------------------------
# Source-of-truth immutability
# ---------------------------------------------------------------------------

class TestSourceOfTruthUnchanged:
    def test_working_state_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        before = (state_dir / "working_state.yaml").read_text()
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        assert (state_dir / "working_state.yaml").read_text() == before

    def test_decision_log_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        before = (state_dir / "decision_log.yaml").read_text()
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        assert (state_dir / "decision_log.yaml").read_text() == before

    def test_charter_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        before = (state_dir / "project_charter.md").read_text()
        ingest_round_run(state_dir, r.round_id, write_artifact(tmp_path), "test-project")
        assert (state_dir / "project_charter.md").read_text() == before
