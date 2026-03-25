"""Tests for Phase 11 round progression / status transitions."""
import json
from pathlib import Path

import pytest

from src.models import RoundState
from src.services.round_service import (
    start_round,
    ingest_round_run,
    generate_round_review,
    generate_round_proposal,
    generate_round_escalation,
    close_round,
    get_round_state,
    RoundError,
)


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

ARTIFACT_PARTIAL = {
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

ARTIFACT_SUCCESS = {
    **ARTIFACT_PARTIAL,
    "status": "success",
    "tests_run": ["test_basic — PASS", "test_edge — PASS"],
    "unresolved_items": [],
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


def write_artifact(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "artifact.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _load_state(state_dir: Path, round_id: str) -> RoundState:
    path = state_dir / "rounds" / round_id / "round_state.json"
    return RoundState(**json.loads(path.read_text()))


# ---------------------------------------------------------------------------
# Status transitions — step by step
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    def test_start_round_creates_task_ready(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        state = _load_state(state_dir, r.round_id)
        assert state.status == "task_ready"

    def test_ingest_sets_run_received(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        state = _load_state(state_dir, r.round_id)
        assert state.status == "run_received"

    def test_review_sets_review_ready(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        state = _load_state(state_dir, r.round_id)
        assert state.status == "review_ready"

    def test_proposal_sets_proposal_ready(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        state = _load_state(state_dir, r.round_id)
        assert state.status == "proposal_ready"

    def test_escalation_sets_escalation_ready_when_not_none(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        packet, _ = generate_round_escalation(state_dir, r.round_id)
        assert packet.category != "none"
        state = _load_state(state_dir, r.round_id)
        assert state.status == "escalation_ready"

    def test_escalation_keeps_proposal_ready_when_none_category(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_SUCCESS), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        packet, _ = generate_round_escalation(state_dir, r.round_id)
        assert packet.category == "none"
        state = _load_state(state_dir, r.round_id)
        assert state.status == "proposal_ready"

    def test_close_round_sets_closed(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_SUCCESS), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        close_round(state_dir, r.round_id)
        state = _load_state(state_dir, r.round_id)
        assert state.status == "closed"

    def test_close_round_applies_proposal(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_SUCCESS), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        result = close_round(state_dir, r.round_id)
        # SUCCESS artifact → proposal has progress additions + goal update
        assert result.working_state_modified


# ---------------------------------------------------------------------------
# Artifact presence flags
# ---------------------------------------------------------------------------

class TestArtifactFlags:
    def test_has_run_artifact_set_after_ingest(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        assert _load_state(state_dir, r.round_id).has_run_artifact is True

    def test_has_review_packet_set_after_review(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        assert _load_state(state_dir, r.round_id).has_review_packet is True

    def test_has_proposal_set_after_proposal(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        assert _load_state(state_dir, r.round_id).has_proposal is True

    def test_has_escalation_set_after_escalation(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        generate_round_escalation(state_dir, r.round_id)
        assert _load_state(state_dir, r.round_id).has_escalation is True

    def test_escalation_category_stored(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        packet, _ = generate_round_escalation(state_dir, r.round_id)
        state = _load_state(state_dir, r.round_id)
        assert state.escalation_category == packet.category

    def test_updated_at_changes_on_each_transition(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        t0 = _load_state(state_dir, r.round_id).updated_at
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        t1 = _load_state(state_dir, r.round_id).updated_at
        assert t1 is not None
        assert t1 != t0


# ---------------------------------------------------------------------------
# get_round_state
# ---------------------------------------------------------------------------

class TestGetRoundState:
    def test_returns_round_state(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        state = get_round_state(state_dir, r.round_id)
        assert isinstance(state, RoundState)
        assert state.round_id == r.round_id
        assert state.status == "task_ready"

    def test_missing_round_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        with pytest.raises(RoundError, match="does not exist"):
            get_round_state(state_dir, "round-0099")


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_old_round_state_loads_without_new_fields(self, tmp_path):
        state_dir = setup_project(tmp_path)
        round_dir = state_dir / "rounds" / "round-0001"
        round_dir.mkdir(parents=True)
        old_state = {
            "round_id": "round-0001",
            "project_name": "test-project",
            "created_at": "2026-03-24T09:00:00+00:00",
            "status": "task_ready",
            "source_task_role": "claude",
            "based_on_phase": "Phase 10",
            "based_on_goal": "Some goal.",
        }
        (round_dir / "round_state.json").write_text(json.dumps(old_state), encoding="utf-8")

        state = get_round_state(state_dir, "round-0001")
        assert state.has_run_artifact is False
        assert state.has_review_packet is False
        assert state.has_proposal is False
        assert state.has_escalation is False
        assert state.escalation_category is None

    def test_old_round_can_be_progressed(self, tmp_path):
        state_dir = setup_project(tmp_path)
        round_dir = state_dir / "rounds" / "round-0001"
        round_dir.mkdir(parents=True)
        old_state = {
            "round_id": "round-0001",
            "project_name": "test-project",
            "created_at": "2026-03-24T09:00:00+00:00",
            "status": "task_ready",
            "source_task_role": "claude",
            "based_on_phase": "Phase 10",
            "based_on_goal": "Some goal.",
        }
        (round_dir / "round_state.json").write_text(json.dumps(old_state), encoding="utf-8")

        ingest_round_run(state_dir, "round-0001",
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        state = get_round_state(state_dir, "round-0001")
        assert state.status == "run_received"
        assert state.has_run_artifact is True


# ---------------------------------------------------------------------------
# Source-of-truth unchanged (status transitions only)
# ---------------------------------------------------------------------------

class TestNoUnintendedMutation:
    def test_status_transitions_do_not_modify_working_state(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "working_state.yaml").read_text()
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_PARTIAL), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        generate_round_escalation(state_dir, r.round_id)
        assert (state_dir / "working_state.yaml").read_text() == before

    def test_close_round_modifies_working_state_via_apply(self, tmp_path):
        # close_round IS allowed to modify working_state via Phase 7 apply behavior
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        ingest_round_run(state_dir, r.round_id,
                         write_artifact(tmp_path, ARTIFACT_SUCCESS), "test-project")
        generate_round_review(state_dir, r.round_id)
        generate_round_proposal(state_dir, r.round_id)
        before = (state_dir / "working_state.yaml").read_text()
        close_round(state_dir, r.round_id)
        # SUCCESS artifact → proposal has additions → working_state was modified
        after = (state_dir / "working_state.yaml").read_text()
        assert after != before
