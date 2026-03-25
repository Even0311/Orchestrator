"""Tests for Phase 5 controlled state update proposal generation."""
import json
import pytest
from pathlib import Path

from src.models import StateUpdateProposal, ImplementationRunArtifact, ReviewPacket
from src.models.working_state import WorkingState, Risk, Progress
from src.services.proposal_service import (
    generate_state_update_proposal,
    save_state_update_proposal,
    ProposalError,
    _propose_progress_additions,
    _propose_next_step_update,
    _propose_current_goal_update,
    _propose_risk_updates,
    _propose_decision_log_candidates,
    _find_failing_tests,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CHARTER = """\
# Charter

## 项目概述

Test project overview.

---

## Core Principles

- **Principle**: Keep it simple.
"""

WORKING_STATE_YAML = """\
project_name: test-project
current_phase: Phase 10
current_goal: Implement feature Y.
next_expected_step: Run integration tests and verify output.
context_notes: Background context.
recent_progress:
  - item: Task A completed
    completed: true
  - item: Task B pending
    completed: false
  - item: Task C pending
    completed: false
current_risks:
  - description: High risk alpha
    severity: high
    mitigation: Mitigate alpha
"""

DECISION_LOG_YAML = """\
decisions:
  - date: "2026-03-20"
    title: Decision A
    decision: We chose A.
    rationale: Simpler.
"""

ARTIFACT_PARTIAL = {
    "project_name": "test-project",
    "generated_at": "2026-03-24T09:00:00+00:00",
    "role": "claude",
    "task_summary": "Implement Phase 10 feature Y.",
    "status": "partial",
    "files_changed": ["src/feature_y.py", "tests/test_feature_y.py"],
    "implemented_items": ["Added feature_y() function", "Wired into pipeline"],
    "tests_run": ["test_feature_y_basic — PASS", "test_feature_y_edge — FAIL"],
    "unresolved_items": ["test_feature_y_edge still failing — edge case not handled"],
    "notes": "Core path works. Edge case needs a fix.",
}

ARTIFACT_SUCCESS = {
    **ARTIFACT_PARTIAL,
    "status": "success",
    "tests_run": ["test_feature_y_basic — PASS", "test_feature_y_edge — PASS"],
    "unresolved_items": [],
    "notes": "All tests passing.",
}

ARTIFACT_FAILED = {
    **ARTIFACT_PARTIAL,
    "status": "failed",
    "implemented_items": [],
    "tests_run": ["test_feature_y_basic — FAIL"],
    "unresolved_items": ["Feature Y not implemented — approach needs rethink"],
}

REVIEW_PACKET = {
    "generated_at": "2026-03-24T09:05:00+00:00",
    "project_name": "test-project",
    "current_phase": "Phase 10",
    "current_goal": "Implement feature Y.",
    "project_summary": "Test project overview.",
    "recent_progress": [],
    "current_risks": [],
    "recent_decisions": [],
    "run_summary": {
        "task_summary": "Implement Phase 10 feature Y.",
        "status": "partial",
        "files_changed": [],
        "implemented_items": [],
        "tests_run": [],
        "unresolved_items": ["test_feature_y_edge still failing"],
    },
    "inspect_next": "test_feature_y_edge still failing — edge case not handled",
}


def setup_project(tmp_path: Path, artifact_data: dict = None, review_data: dict = None) -> Path:
    state_dir = tmp_path / "projects" / "test-project"
    state_dir.mkdir(parents=True)
    (state_dir / "project_charter.md").write_text(CHARTER, encoding="utf-8")
    (state_dir / "working_state.yaml").write_text(WORKING_STATE_YAML, encoding="utf-8")
    (state_dir / "decision_log.yaml").write_text(DECISION_LOG_YAML, encoding="utf-8")

    artifacts_dir = state_dir / "artifacts"
    artifacts_dir.mkdir()
    data = artifact_data or ARTIFACT_PARTIAL
    (artifacts_dir / "run_2026-03-24T09-00-00.json").write_text(
        json.dumps(data), encoding="utf-8"
    )

    review = review_data or REVIEW_PACKET
    (state_dir / "review_packet.json").write_text(
        json.dumps(review), encoding="utf-8"
    )

    return state_dir


def make_artifact(**overrides) -> ImplementationRunArtifact:
    data = {**ARTIFACT_PARTIAL, **overrides}
    return ImplementationRunArtifact(**data)


def make_state(**overrides) -> WorkingState:
    defaults = dict(
        project_name="test-project",
        current_phase="Phase 10",
        current_goal="Implement feature Y.\n",
        next_expected_step="Run integration tests and verify output.\n",
        recent_progress=[
            Progress(item="Task A completed", completed=True),
            Progress(item="Task B pending", completed=False),
        ],
        current_risks=[Risk(description="High risk alpha", severity="high")],
    )
    defaults.update(overrides)
    return WorkingState(**defaults)


def make_review(**overrides) -> ReviewPacket:
    from src.models.review_packet import RunSummary
    defaults = dict(
        generated_at="2026-03-24T09:05:00+00:00",
        project_name="test-project",
        current_phase="Phase 10",
        current_goal="Implement feature Y.",
        project_summary="Test project overview.",
        run_summary=RunSummary(
            task_summary="Task",
            status="partial",
            unresolved_items=["edge case not handled"],
        ),
        inspect_next="edge case not handled",
    )
    defaults.update(overrides)
    return ReviewPacket(**defaults)


# ---------------------------------------------------------------------------
# _find_failing_tests
# ---------------------------------------------------------------------------

class TestFindFailingTests:
    def test_finds_fail(self):
        assert _find_failing_tests(["test_a — PASS", "test_b — FAIL"]) == ["test_b — FAIL"]

    def test_finds_failed(self):
        assert _find_failing_tests(["test_b — FAILED"]) == ["test_b — FAILED"]

    def test_finds_error(self):
        assert _find_failing_tests(["test_b — ERROR"]) == ["test_b — ERROR"]

    def test_empty_when_all_pass(self):
        assert _find_failing_tests(["test_a — PASS", "test_b — PASS"]) == []

    def test_empty_list(self):
        assert _find_failing_tests([]) == []


# ---------------------------------------------------------------------------
# _propose_progress_additions
# ---------------------------------------------------------------------------

class TestProposeProgressAdditions:
    def test_returns_implemented_items(self):
        artifact = make_artifact()
        result = _propose_progress_additions(artifact)
        assert result == ARTIFACT_PARTIAL["implemented_items"]

    def test_empty_when_no_implemented_items(self):
        artifact = make_artifact(implemented_items=[])
        assert _propose_progress_additions(artifact) == []


# ---------------------------------------------------------------------------
# _propose_next_step_update
# ---------------------------------------------------------------------------

class TestProposeNextStepUpdate:
    def test_unresolved_items_take_priority(self):
        artifact = make_artifact(unresolved_items=["Fix edge case X"])
        state = make_state()
        review = make_review(inspect_next="something else")
        proposed, rationale = _propose_next_step_update(artifact, state, review)
        assert proposed == "Fix edge case X"
        assert "unresolved" in rationale.lower()

    def test_multiple_unresolved_joined(self):
        artifact = make_artifact(unresolved_items=["Issue A", "Issue B"])
        state = make_state()
        review = make_review()
        proposed, _ = _propose_next_step_update(artifact, state, review)
        assert "Issue A" in proposed
        assert "Issue B" in proposed

    def test_falls_back_to_inspect_next_when_different(self):
        artifact = make_artifact(unresolved_items=[])
        state = make_state(next_expected_step="Old step.")
        review = make_review(inspect_next="New step from review.")
        proposed, rationale = _propose_next_step_update(artifact, state, review)
        assert proposed == "New step from review."
        assert "inspect_next" in rationale.lower()

    def test_no_update_when_step_unchanged(self):
        artifact = make_artifact(unresolved_items=[])
        state = make_state(next_expected_step="Run integration tests and verify output.")
        review = make_review(inspect_next="Run integration tests and verify output.")
        proposed, rationale = _propose_next_step_update(artifact, state, review)
        assert proposed is None
        assert "applicable" in rationale.lower()


# ---------------------------------------------------------------------------
# _propose_current_goal_update
# ---------------------------------------------------------------------------

class TestProposeCurrentGoalUpdate:
    def test_success_proposes_update(self):
        artifact = make_artifact(status="success")
        state = make_state()
        proposed, rationale = _propose_current_goal_update(artifact, state)
        assert proposed is not None
        assert "success" in rationale.lower()

    def test_partial_proposes_nothing(self):
        artifact = make_artifact(status="partial")
        state = make_state()
        proposed, _ = _propose_current_goal_update(artifact, state)
        assert proposed is None

    def test_failed_proposes_nothing(self):
        artifact = make_artifact(status="failed")
        state = make_state()
        proposed, _ = _propose_current_goal_update(artifact, state)
        assert proposed is None


# ---------------------------------------------------------------------------
# _propose_risk_updates
# ---------------------------------------------------------------------------

class TestProposeRiskUpdates:
    def test_unresolved_item_becomes_risk_candidate(self):
        artifact = make_artifact(unresolved_items=["Edge case not handled"])
        state = make_state(current_risks=[])
        risks = _propose_risk_updates(artifact, state)
        assert any("Edge case not handled" in r for r in risks)

    def test_failing_test_becomes_risk_candidate(self):
        artifact = make_artifact(
            unresolved_items=[],
            tests_run=["test_edge — FAIL"],
        )
        state = make_state(current_risks=[])
        risks = _propose_risk_updates(artifact, state)
        assert any("test_edge" in r for r in risks)

    def test_no_risk_when_all_pass_and_no_unresolved(self):
        artifact = make_artifact(
            unresolved_items=[],
            tests_run=["test_a — PASS"],
        )
        state = make_state()
        risks = _propose_risk_updates(artifact, state)
        assert risks == []

    def test_existing_risk_not_duplicated(self):
        artifact = make_artifact(unresolved_items=["High risk alpha"])
        state = make_state(
            current_risks=[Risk(description="High risk alpha", severity="high")]
        )
        risks = _propose_risk_updates(artifact, state)
        # already in existing risks → should not appear
        assert not any("High risk alpha" in r for r in risks)


# ---------------------------------------------------------------------------
# _propose_decision_log_candidates
# ---------------------------------------------------------------------------

class TestProposeDecisionLogCandidates:
    def test_success_produces_candidate(self):
        artifact = make_artifact(status="success")
        state = make_state()
        candidates = _propose_decision_log_candidates(artifact, state)
        assert len(candidates) == 1
        assert "implementation approach" in candidates[0].lower()

    def test_partial_with_unresolved_produces_candidate(self):
        artifact = make_artifact(status="partial", unresolved_items=["Issue X"])
        state = make_state()
        candidates = _propose_decision_log_candidates(artifact, state)
        assert len(candidates) == 1
        assert "resolution" in candidates[0].lower()

    def test_failed_with_no_unresolved_produces_nothing(self):
        artifact = make_artifact(status="failed", unresolved_items=[])
        state = make_state()
        candidates = _propose_decision_log_candidates(artifact, state)
        assert candidates == []


# ---------------------------------------------------------------------------
# generate_state_update_proposal (integration)
# ---------------------------------------------------------------------------

class TestGenerateStateUpdateProposal:
    def test_generates_valid_proposal(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert isinstance(proposal, StateUpdateProposal)

    def test_project_name_from_working_state(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert proposal.project_name == "test-project"

    def test_based_on_references_artifact_and_review(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert "run_" in proposal.based_on.artifact_path
        assert "review_packet" in proposal.based_on.review_packet_path

    def test_progress_additions_from_implemented_items(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert "Added feature_y() function" in proposal.proposed_recent_progress_additions
        assert "Wired into pipeline" in proposal.proposed_recent_progress_additions

    def test_progress_updates_always_empty(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert proposal.proposed_recent_progress_updates == []

    def test_no_goal_update_for_partial(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert proposal.proposed_current_goal_update is None

    def test_goal_update_for_success(self, tmp_path):
        review = {**REVIEW_PACKET, "run_summary": {**REVIEW_PACKET["run_summary"], "status": "success"}}
        state_dir = setup_project(tmp_path, artifact_data=ARTIFACT_SUCCESS, review_data=review)
        proposal = generate_state_update_proposal(state_dir)
        assert proposal.proposed_current_goal_update is not None

    def test_next_step_update_from_unresolved(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert proposal.proposed_next_expected_step_update is not None
        assert "edge" in proposal.proposed_next_expected_step_update.lower()

    def test_risk_update_from_failing_test(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert any("FAIL" in r or "failing" in r.lower() or "edge" in r.lower()
                   for r in proposal.proposed_risk_updates)

    def test_explicitly_unchanged_always_has_charter(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert any("project_charter" in u for u in proposal.explicitly_unchanged)

    def test_explicitly_unchanged_always_has_current_phase(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert any("current_phase" in u for u in proposal.explicitly_unchanged)

    def test_explicitly_unchanged_lists_pending_items(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert any("pending" in u.lower() for u in proposal.explicitly_unchanged)

    def test_rationale_notes_populated(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        assert len(proposal.rationale_notes) > 0

    def test_no_review_packet_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        (state_dir / "review_packet.json").unlink()
        with pytest.raises(ProposalError, match="review_packet"):
            generate_state_update_proposal(state_dir)

    def test_no_artifacts_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        for f in (state_dir / "artifacts").glob("*.json"):
            f.unlink()
        with pytest.raises(ProposalError):
            generate_state_update_proposal(state_dir)

    def test_source_of_truth_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "working_state.yaml").read_text()
        generate_state_update_proposal(state_dir)
        after = (state_dir / "working_state.yaml").read_text()
        assert before == after


# ---------------------------------------------------------------------------
# save_state_update_proposal
# ---------------------------------------------------------------------------

class TestSaveStateUpdateProposal:
    def test_saved_to_expected_path(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        saved = save_state_update_proposal(proposal, state_dir)
        assert saved == state_dir / "state_update_proposal.json"
        assert saved.exists()

    def test_saved_content_is_valid_json(self, tmp_path):
        state_dir = setup_project(tmp_path)
        proposal = generate_state_update_proposal(state_dir)
        saved = save_state_update_proposal(proposal, state_dir)
        data = json.loads(saved.read_text(encoding="utf-8"))
        assert "based_on" in data
        assert "explicitly_unchanged" in data
        assert "proposed_recent_progress_additions" in data
