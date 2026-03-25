"""Tests for Phase 13 — Claude adapter stub / local invocation boundary."""
import json
from pathlib import Path

import pytest

from src.models import ClaudeInvocation
from src.services.round_service import start_round, RoundError
from src.services.submission_service import prepare_round_submission
from src.services.invocation_service import (
    prepare_round_invocation,
    InvocationError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WORKING_STATE_YAML = """\
project_name: test-project
current_phase: Phase 13
current_goal: Implement invocation boundary.
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


def _setup_ready_round(tmp_path: Path):
    """Start a round and prepare the submission artifacts so invocation can proceed."""
    state_dir = setup_project(tmp_path)
    r = start_round(state_dir)
    prepare_round_submission(state_dir, r.round_id)
    return state_dir, r.round_id


# ---------------------------------------------------------------------------
# Valid generation
# ---------------------------------------------------------------------------

class TestPrepareRoundInvocation:
    def test_writes_descriptor_to_round_dir(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        result = prepare_round_invocation(state_dir, round_id)
        assert result.invocation_path.exists()
        assert result.invocation_path.name == "claude_invocation.json"
        assert result.invocation_path.parent == result.round_dir

    def test_descriptor_is_valid_json(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        result = prepare_round_invocation(state_dir, round_id)
        data = json.loads(result.invocation_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_descriptor_validates_as_pydantic_model(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        result = prepare_round_invocation(state_dir, round_id)
        data = json.loads(result.invocation_path.read_text(encoding="utf-8"))
        inv = ClaudeInvocation(**data)
        assert inv.adapter_mode == "manual_stub"


# ---------------------------------------------------------------------------
# Descriptor content
# ---------------------------------------------------------------------------

class TestDescriptorContent:
    def _descriptor(self, tmp_path) -> dict:
        state_dir, round_id = _setup_ready_round(tmp_path)
        result = prepare_round_invocation(state_dir, round_id)
        return json.loads(result.invocation_path.read_text(encoding="utf-8"))

    def test_project_name_correct(self, tmp_path):
        assert self._descriptor(tmp_path)["project_name"] == "test-project"

    def test_round_id_correct(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        prepare_round_submission(state_dir, r.round_id)
        result = prepare_round_invocation(state_dir, r.round_id)
        data = json.loads(result.invocation_path.read_text(encoding="utf-8"))
        assert data["round_id"] == r.round_id

    def test_adapter_mode_is_manual_stub(self, tmp_path):
        assert self._descriptor(tmp_path)["adapter_mode"] == "manual_stub"

    def test_generated_at_present(self, tmp_path):
        assert "generated_at" in self._descriptor(tmp_path)

    def test_input_files_present(self, tmp_path):
        d = self._descriptor(tmp_path)
        assert "input_files" in d
        inp = d["input_files"]
        assert inp["task_file"] == "task_for_claude.md"
        assert inp["submission_envelope"] == "claude_submission_envelope.json"
        assert inp["artifact_template"] == "run_artifact_template.json"

    def test_expected_output_file_present(self, tmp_path):
        d = self._descriptor(tmp_path)
        assert d["expected_output_file"] == "run_artifact.json"

    def test_invocation_preview_present(self, tmp_path):
        d = self._descriptor(tmp_path)
        assert "invocation_preview" in d
        assert len(d["invocation_preview"]) > 0

    def test_preview_mentions_project_and_round(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        prepare_round_submission(state_dir, r.round_id)
        result = prepare_round_invocation(state_dir, r.round_id)
        data = json.loads(result.invocation_path.read_text(encoding="utf-8"))
        preview = data["invocation_preview"]
        assert "test-project" in preview
        assert r.round_id in preview

    def test_preview_mentions_ingest_step(self, tmp_path):
        preview = self._descriptor(tmp_path)["invocation_preview"]
        assert "ingest-round-run" in preview

    def test_preview_mentions_next_orchestrator_step(self, tmp_path):
        preview = self._descriptor(tmp_path)["invocation_preview"]
        assert "review-round" in preview

    def test_preview_mentions_expected_output(self, tmp_path):
        preview = self._descriptor(tmp_path)["invocation_preview"]
        assert "run_artifact.json" in preview


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestErrorCases:
    def test_missing_round_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        with pytest.raises((RoundError, InvocationError)):
            prepare_round_invocation(state_dir, "round-0099")

    def test_missing_task_file_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        # task_for_claude.md exists but submission artifacts do not
        with pytest.raises((RoundError, InvocationError)):
            prepare_round_invocation(state_dir, r.round_id)

    def test_missing_submission_envelope_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        round_dir = state_dir / "rounds" / r.round_id
        # Place only task file — envelope missing
        assert (round_dir / "task_for_claude.md").exists()
        with pytest.raises((RoundError, InvocationError)):
            prepare_round_invocation(state_dir, r.round_id)

    def test_missing_artifact_template_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        round_dir = state_dir / "rounds" / r.round_id
        (round_dir / "claude_submission_envelope.json").write_text("{}", encoding="utf-8")
        # template still missing
        with pytest.raises((RoundError, InvocationError)):
            prepare_round_invocation(state_dir, r.round_id)


# ---------------------------------------------------------------------------
# No mutation
# ---------------------------------------------------------------------------

class TestNoMutation:
    def test_round_state_unchanged(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        before = (state_dir / "rounds" / round_id / "round_state.json").read_text()
        prepare_round_invocation(state_dir, round_id)
        after = (state_dir / "rounds" / round_id / "round_state.json").read_text()
        assert after == before

    def test_working_state_unchanged(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        before = (state_dir / "working_state.yaml").read_text()
        prepare_round_invocation(state_dir, round_id)
        assert (state_dir / "working_state.yaml").read_text() == before

    def test_decision_log_unchanged(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        before = (state_dir / "decision_log.yaml").read_text()
        prepare_round_invocation(state_dir, round_id)
        assert (state_dir / "decision_log.yaml").read_text() == before

    def test_project_charter_unchanged(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        before = (state_dir / "project_charter.md").read_text()
        prepare_round_invocation(state_dir, round_id)
        assert (state_dir / "project_charter.md").read_text() == before

    def test_does_not_create_run_artifact(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        prepare_round_invocation(state_dir, round_id)
        assert not (state_dir / "rounds" / round_id / "run_artifact.json").exists()


# ---------------------------------------------------------------------------
# Deterministic regeneration
# ---------------------------------------------------------------------------

class TestDeterministicRegeneration:
    def test_regeneration_overwrites_descriptor(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        r1 = prepare_round_invocation(state_dir, round_id)
        r1.invocation_path.write_text("{}", encoding="utf-8")
        r2 = prepare_round_invocation(state_dir, round_id)
        data = json.loads(r2.invocation_path.read_text(encoding="utf-8"))
        assert data["project_name"] == "test-project"

    def test_regeneration_stable_content(self, tmp_path):
        state_dir, round_id = _setup_ready_round(tmp_path)
        r1 = prepare_round_invocation(state_dir, round_id)
        d1 = json.loads(r1.invocation_path.read_text(encoding="utf-8"))
        r2 = prepare_round_invocation(state_dir, round_id)
        d2 = json.loads(r2.invocation_path.read_text(encoding="utf-8"))
        # All fields except generated_at should be identical
        for key in ("project_name", "round_id", "adapter_mode", "input_files",
                    "expected_output_file", "invocation_preview"):
            assert d1[key] == d2[key]
