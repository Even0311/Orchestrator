"""Tests for Phase 6 escalation packet generation."""
import json
import pytest
from pathlib import Path

from src.models import EscalationPacket, ImplementationRunArtifact, StateUpdateProposal
from src.models.escalation_packet import CATEGORY_SEVERITY
from src.services.escalation_service import (
    generate_escalation_packet,
    save_escalation_packet,
    EscalationError,
    _is_implementation_blocked,
    _is_state_conflict,
    _is_decision_required,
    _is_review_attention_required,
    _evaluate_category,
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

REVIEW_PACKET = {
    "generated_at": "2026-03-24T09:05:00+00:00",
    "project_name": "test-project",
    "current_phase": "Phase 10",
    "current_goal": "Implement feature Y.",
    "project_summary": "Overview.",
    "recent_progress": [],
    "current_risks": [],
    "recent_decisions": [],
    "run_summary": {
        "task_summary": "Task",
        "status": "partial",
        "files_changed": [],
        "implemented_items": [],
        "tests_run": [],
        "unresolved_items": [],
    },
    "inspect_next": "Fix failing test.",
}

PROPOSAL_BASE = {
    "generated_at": "2026-03-24T09:10:00+00:00",
    "project_name": "test-project",
    "based_on": {
        "artifact_path": "/fake/artifact.json",
        "review_packet_path": "/fake/review_packet.json",
    },
    "proposed_recent_progress_additions": [],
    "proposed_recent_progress_updates": [],
    "proposed_current_goal_update": None,
    "proposed_next_expected_step_update": None,
    "proposed_risk_updates": [],
    "proposed_decision_log_candidates": [],
    "explicitly_unchanged": ["project_charter.md"],
    "rationale_notes": [],
}

ARTIFACT_BASE = {
    "project_name": "test-project",
    "generated_at": "2026-03-24T09:00:00+00:00",
    "role": "claude",
    "task_summary": "Implement feature Y.",
    "status": "partial",
    "files_changed": ["src/feature_y.py"],
    "implemented_items": ["Added feature_y()"],
    "tests_run": ["test_basic — PASS", "test_edge — FAIL"],
    "unresolved_items": ["test_edge failing"],
}


def setup_project(
    tmp_path: Path,
    artifact_data: dict = None,
    proposal_data: dict = None,
) -> Path:
    state_dir = tmp_path / "projects" / "test-project"
    state_dir.mkdir(parents=True)
    (state_dir / "project_charter.md").write_text("# Charter\n\n## 项目概述\nOverview.\n")
    (state_dir / "working_state.yaml").write_text(WORKING_STATE_YAML, encoding="utf-8")
    (state_dir / "decision_log.yaml").write_text("decisions: []\n", encoding="utf-8")
    (state_dir / "review_packet.json").write_text(json.dumps(REVIEW_PACKET), encoding="utf-8")

    artifacts_dir = state_dir / "artifacts"
    artifacts_dir.mkdir()
    art = artifact_data or ARTIFACT_BASE
    (artifacts_dir / "run_2026-03-24T09-00-00.json").write_text(json.dumps(art), encoding="utf-8")

    prop = proposal_data or PROPOSAL_BASE
    (state_dir / "state_update_proposal.json").write_text(json.dumps(prop), encoding="utf-8")

    return state_dir


def make_artifact(**overrides) -> ImplementationRunArtifact:
    return ImplementationRunArtifact(**{**ARTIFACT_BASE, **overrides})


def make_proposal(**overrides) -> StateUpdateProposal:
    return StateUpdateProposal(**{**PROPOSAL_BASE, **overrides})


# ---------------------------------------------------------------------------
# Individual trigger rules
# ---------------------------------------------------------------------------

class TestIsImplementationBlocked:
    def test_failed_status(self):
        assert _is_implementation_blocked(make_artifact(status="failed"))

    def test_partial_no_progress_with_unresolved(self):
        assert _is_implementation_blocked(
            make_artifact(status="partial", implemented_items=[], unresolved_items=["X"])
        )

    def test_partial_with_progress_not_blocked(self):
        assert not _is_implementation_blocked(
            make_artifact(status="partial", implemented_items=["Done something"],
                          unresolved_items=["X"])
        )

    def test_success_not_blocked(self):
        assert not _is_implementation_blocked(make_artifact(status="success", unresolved_items=[]))

    def test_partial_no_unresolved_not_blocked(self):
        assert not _is_implementation_blocked(
            make_artifact(status="partial", implemented_items=[], unresolved_items=[])
        )


class TestIsStateConflict:
    def test_goal_update_with_risks_is_conflict(self):
        artifact = make_artifact(status="success")
        proposal = make_proposal(
            proposed_current_goal_update="Phase complete.",
            proposed_risk_updates=["[NEW RISK] Something"],
        )
        assert _is_state_conflict(artifact, proposal)

    def test_goal_update_without_risks_is_not_conflict(self):
        artifact = make_artifact(status="success")
        proposal = make_proposal(proposed_current_goal_update="Phase complete.")
        assert not _is_state_conflict(artifact, proposal)

    def test_no_goal_update_not_conflict(self):
        artifact = make_artifact()
        proposal = make_proposal(proposed_risk_updates=["Some risk"])
        assert not _is_state_conflict(artifact, proposal)


class TestIsDecisionRequired:
    def test_decision_candidate_and_step_change(self):
        proposal = make_proposal(
            proposed_decision_log_candidates=["Consider documenting X"],
            proposed_next_expected_step_update="New step.",
        )
        assert _is_decision_required(proposal)

    def test_decision_candidate_without_step_change(self):
        proposal = make_proposal(proposed_decision_log_candidates=["Consider X"])
        assert not _is_decision_required(proposal)

    def test_step_change_without_decision_candidate(self):
        proposal = make_proposal(proposed_next_expected_step_update="New step.")
        assert not _is_decision_required(proposal)

    def test_neither(self):
        assert not _is_decision_required(make_proposal())


class TestIsReviewAttentionRequired:
    def test_partial_with_unresolved(self):
        artifact = make_artifact(status="partial", unresolved_items=["X"])
        assert _is_review_attention_required(artifact, make_proposal())

    def test_new_risks_in_proposal(self):
        artifact = make_artifact(status="success", unresolved_items=[])
        proposal = make_proposal(proposed_risk_updates=["Risk candidate"])
        assert _is_review_attention_required(artifact, proposal)

    def test_success_no_risks_no_unresolved(self):
        artifact = make_artifact(status="success", unresolved_items=[])
        assert not _is_review_attention_required(artifact, make_proposal())


# ---------------------------------------------------------------------------
# _evaluate_category — precedence
# ---------------------------------------------------------------------------

class TestEvaluateCategory:
    def test_blocked_wins_over_all(self):
        artifact = make_artifact(status="failed")
        proposal = make_proposal(
            proposed_decision_log_candidates=["X"],
            proposed_next_expected_step_update="Y",
            proposed_risk_updates=["R"],
        )
        assert _evaluate_category(artifact, proposal) == "implementation_blocked"

    def test_state_conflict_wins_over_decision_and_review(self):
        artifact = make_artifact(status="success", unresolved_items=[])
        proposal = make_proposal(
            proposed_current_goal_update="Done.",
            proposed_risk_updates=["New risk"],
            proposed_decision_log_candidates=["Consider X"],
            proposed_next_expected_step_update="Next step",
        )
        assert _evaluate_category(artifact, proposal) == "state_conflict_detected"

    def test_decision_required_wins_over_review(self):
        artifact = make_artifact(status="partial", unresolved_items=["X"],
                                 implemented_items=["done"])
        proposal = make_proposal(
            proposed_decision_log_candidates=["Consider X"],
            proposed_next_expected_step_update="New step.",
        )
        assert _evaluate_category(artifact, proposal) == "decision_required"

    def test_review_attention_fallback(self):
        artifact = make_artifact(status="partial", unresolved_items=["X"],
                                 implemented_items=["done"])
        assert _evaluate_category(artifact, make_proposal()) == "review_attention_required"

    def test_none_when_clean(self):
        artifact = make_artifact(status="success", unresolved_items=[], implemented_items=[])
        assert _evaluate_category(artifact, make_proposal()) == "none"


# ---------------------------------------------------------------------------
# generate_escalation_packet (integration)
# ---------------------------------------------------------------------------

class TestGenerateEscalationPacket:
    def test_generates_valid_packet(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        assert isinstance(packet, EscalationPacket)

    def test_blocked_for_failed_artifact(self, tmp_path):
        state_dir = setup_project(tmp_path, artifact_data={**ARTIFACT_BASE, "status": "failed"})
        packet = generate_escalation_packet(state_dir)
        assert packet.category == "implementation_blocked"
        assert packet.severity == "high"

    def test_review_attention_for_partial_with_unresolved(self, tmp_path):
        # partial + implemented_items present → not blocked → falls to review_attention
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        assert packet.category == "review_attention_required"
        assert packet.severity == "low"

    def test_none_for_clean_success(self, tmp_path):
        clean_artifact = {
            **ARTIFACT_BASE,
            "status": "success",
            "unresolved_items": [],
            "tests_run": ["test_basic — PASS"],
        }
        state_dir = setup_project(tmp_path, artifact_data=clean_artifact)
        packet = generate_escalation_packet(state_dir)
        assert packet.category == "none"
        assert packet.severity == "none"

    def test_evidence_contains_unresolved_items(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        assert "test_edge failing" in packet.evidence.unresolved_items

    def test_evidence_contains_artifact_status(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        assert packet.evidence.artifact_status == "partial"

    def test_escalation_has_recommended_action(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        assert packet.recommended_human_action

    def test_escalation_has_explicitly_not_decided(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        assert len(packet.explicitly_not_decided_by_system) > 0

    def test_none_has_empty_not_decided(self, tmp_path):
        clean = {**ARTIFACT_BASE, "status": "success", "unresolved_items": [],
                 "tests_run": ["test — PASS"]}
        state_dir = setup_project(tmp_path, artifact_data=clean)
        packet = generate_escalation_packet(state_dir)
        assert packet.explicitly_not_decided_by_system == []

    def test_severity_matches_category(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        assert packet.severity == CATEGORY_SEVERITY[packet.category]

    def test_missing_proposal_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        (state_dir / "state_update_proposal.json").unlink()
        with pytest.raises(EscalationError, match="state_update_proposal"):
            generate_escalation_packet(state_dir)

    def test_missing_artifacts_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        for f in (state_dir / "artifacts").glob("*.json"):
            f.unlink()
        with pytest.raises(EscalationError):
            generate_escalation_packet(state_dir)

    def test_source_of_truth_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "working_state.yaml").read_text()
        generate_escalation_packet(state_dir)
        after = (state_dir / "working_state.yaml").read_text()
        assert before == after


# ---------------------------------------------------------------------------
# save_escalation_packet
# ---------------------------------------------------------------------------

class TestSaveEscalationPacket:
    def test_saved_to_expected_path(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        saved = save_escalation_packet(packet, state_dir)
        assert saved == state_dir / "escalation_packet.json"
        assert saved.exists()

    def test_saved_content_is_valid_json(self, tmp_path):
        state_dir = setup_project(tmp_path)
        packet = generate_escalation_packet(state_dir)
        saved = save_escalation_packet(packet, state_dir)
        data = json.loads(saved.read_text(encoding="utf-8"))
        assert "category" in data
        assert "evidence" in data
        assert "recommended_human_action" in data
