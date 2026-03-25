"""Tests for Phase 12 — Claude runner interface / submission envelope."""
import json
from pathlib import Path

import pytest

from src.models import ClaudeSubmissionEnvelope
from src.services.round_service import start_round, RoundError
from src.services.submission_service import (
    prepare_round_submission,
    SubmissionError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WORKING_STATE_YAML = """\
project_name: test-project
current_phase: Phase 12
current_goal: Implement submission envelope.
next_expected_step: Run integration tests.
recent_progress:
  - item: Task A
    completed: true
current_risks:
  - description: Known risk
    severity: medium
"""


def setup_project(tmp_path: Path) -> Path:
    state_dir = tmp_path / "projects" / "test-project"
    state_dir.mkdir(parents=True)
    (state_dir / "working_state.yaml").write_text(WORKING_STATE_YAML, encoding="utf-8")
    (state_dir / "decision_log.yaml").write_text("decisions: []\n", encoding="utf-8")
    (state_dir / "project_charter.md").write_text(
        "# Charter\n\n## 项目概述\nOverview.\n", encoding="utf-8"
    )
    return state_dir


# ---------------------------------------------------------------------------
# Valid generation
# ---------------------------------------------------------------------------

class TestPrepareRoundSubmission:
    def test_writes_envelope_to_round_dir(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        assert result.envelope_path.exists()
        assert result.envelope_path.name == "claude_submission_envelope.json"
        assert result.envelope_path.parent == result.round_dir

    def test_writes_template_to_round_dir(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        assert result.template_path.exists()
        assert result.template_path.name == "run_artifact_template.json"
        assert result.template_path.parent == result.round_dir

    def test_envelope_is_valid_json(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        data = json.loads(result.envelope_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_template_is_valid_json(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        data = json.loads(result.template_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Envelope content
# ---------------------------------------------------------------------------

class TestEnvelopeContent:
    def _envelope(self, tmp_path) -> dict:
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        return json.loads(result.envelope_path.read_text(encoding="utf-8"))

    def test_project_name_correct(self, tmp_path):
        env = self._envelope(tmp_path)
        assert env["project_name"] == "test-project"

    def test_round_id_correct(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        env = json.loads(result.envelope_path.read_text(encoding="utf-8"))
        assert env["round_id"] == r.round_id

    def test_role_is_claude(self, tmp_path):
        assert self._envelope(tmp_path)["role"] == "claude"

    def test_generated_at_present(self, tmp_path):
        assert "generated_at" in self._envelope(tmp_path)

    def test_current_phase_matches_working_state(self, tmp_path):
        assert self._envelope(tmp_path)["current_phase"] == "Phase 12"

    def test_current_goal_matches_working_state(self, tmp_path):
        assert self._envelope(tmp_path)["current_goal"] == "Implement submission envelope."

    def test_next_expected_step_present(self, tmp_path):
        assert self._envelope(tmp_path)["next_expected_step"] == "Run integration tests."

    def test_deliverables_present(self, tmp_path):
        env = self._envelope(tmp_path)
        assert "deliverables" in env
        assert "description" in env["deliverables"]
        assert "ingest_command" in env["deliverables"]

    def test_ingest_command_contains_project_and_round(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        env = json.loads(result.envelope_path.read_text(encoding="utf-8"))
        cmd = env["deliverables"]["ingest_command"]
        assert "test-project" in cmd
        assert r.round_id in cmd

    def test_round_files_pointer_present(self, tmp_path):
        env = self._envelope(tmp_path)
        assert "round_files" in env
        rf = env["round_files"]
        assert rf["task_file"] == "task_for_claude.md"
        assert rf["task_packet"] == "task_packet_claude.json"
        assert rf["expected_return"] == "run_artifact_template.json"

    def test_envelope_validates_as_pydantic_model(self, tmp_path):
        env = self._envelope(tmp_path)
        parsed = ClaudeSubmissionEnvelope(**env)
        assert parsed.role == "claude"


# ---------------------------------------------------------------------------
# Template content
# ---------------------------------------------------------------------------

class TestTemplateContent:
    def _template(self, tmp_path) -> dict:
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result = prepare_round_submission(state_dir, r.round_id)
        return json.loads(result.template_path.read_text(encoding="utf-8"))

    def test_project_name_is_real_value(self, tmp_path):
        assert self._template(tmp_path)["project_name"] == "test-project"

    def test_role_is_claude(self, tmp_path):
        assert self._template(tmp_path)["role"] == "claude"

    def test_has_required_fields(self, tmp_path):
        t = self._template(tmp_path)
        for field in ("generated_at", "task_summary", "status",
                      "files_changed", "implemented_items", "tests_run", "unresolved_items"):
            assert field in t, f"Missing field: {field}"

    def test_placeholder_fields_are_strings_or_lists(self, tmp_path):
        t = self._template(tmp_path)
        assert isinstance(t["task_summary"], str)
        assert isinstance(t["files_changed"], list)
        assert isinstance(t["unresolved_items"], list)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestErrorCases:
    def test_missing_round_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        with pytest.raises((RoundError, SubmissionError)):
            prepare_round_submission(state_dir, "round-0099")

    def test_missing_task_packet_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        round_dir = state_dir / "rounds" / "round-0001"
        round_dir.mkdir(parents=True)
        (round_dir / "round_state.json").write_text(
            json.dumps({
                "round_id": "round-0001",
                "project_name": "test-project",
                "created_at": "2026-03-24T10:00:00+00:00",
                "status": "task_ready",
                "source_task_role": "claude",
                "based_on_phase": "Phase 12",
                "based_on_goal": "Some goal.",
            }),
            encoding="utf-8",
        )
        with pytest.raises((RoundError, SubmissionError)):
            prepare_round_submission(state_dir, "round-0001")


# ---------------------------------------------------------------------------
# Deterministic regeneration
# ---------------------------------------------------------------------------

class TestDeterministicRegeneration:
    def test_regeneration_overwrites_envelope(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        result1 = prepare_round_submission(state_dir, r.round_id)
        result2 = prepare_round_submission(state_dir, r.round_id)
        assert result2.envelope_path.exists()
        data = json.loads(result2.envelope_path.read_text(encoding="utf-8"))
        assert data["project_name"] == "test-project"

    def test_regeneration_overwrites_template(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        prepare_round_submission(state_dir, r.round_id)
        # Corrupt the template, then regenerate
        result1 = prepare_round_submission(state_dir, r.round_id)
        result1.template_path.write_text("{}", encoding="utf-8")
        result2 = prepare_round_submission(state_dir, r.round_id)
        data = json.loads(result2.template_path.read_text(encoding="utf-8"))
        assert data["project_name"] == "test-project"


# ---------------------------------------------------------------------------
# No source-of-truth mutation
# ---------------------------------------------------------------------------

class TestNoSourceOfTruthMutation:
    def test_working_state_unchanged(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "working_state.yaml").read_text()
        r = start_round(state_dir)
        prepare_round_submission(state_dir, r.round_id)
        assert (state_dir / "working_state.yaml").read_text() == before

    def test_decision_log_unchanged(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "decision_log.yaml").read_text()
        r = start_round(state_dir)
        prepare_round_submission(state_dir, r.round_id)
        assert (state_dir / "decision_log.yaml").read_text() == before

    def test_project_charter_unchanged(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "project_charter.md").read_text()
        r = start_round(state_dir)
        prepare_round_submission(state_dir, r.round_id)
        assert (state_dir / "project_charter.md").read_text() == before

    def test_round_state_unchanged(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        before = (state_dir / "rounds" / r.round_id / "round_state.json").read_text()
        prepare_round_submission(state_dir, r.round_id)
        after = (state_dir / "rounds" / r.round_id / "round_state.json").read_text()
        assert after == before
