"""Tests for Phase 10 round-scoped review / proposal / escalation generation."""
import json
from pathlib import Path

import pytest

from src.services.round_service import (
    start_round,
    ingest_round_run,
    generate_round_review,
    generate_round_proposal,
    generate_round_escalation,
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

CLEAN_ARTIFACT = {
    **ARTIFACT_BASE,
    "status": "success",
    "tests_run": ["test_basic — PASS"],
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


def write_artifact(tmp_path: Path, data: dict = None) -> Path:
    p = tmp_path / "artifact.json"
    p.write_text(json.dumps(data or ARTIFACT_BASE), encoding="utf-8")
    return p


def setup_round_with_artifact(tmp_path: Path, artifact_data: dict = None) -> tuple[Path, str]:
    state_dir = setup_project(tmp_path)
    r = start_round(state_dir)
    artifact_file = write_artifact(tmp_path, artifact_data)
    ingest_round_run(state_dir, r.round_id, artifact_file, "test-project")
    return state_dir, r.round_id


def setup_round_with_review(tmp_path: Path, artifact_data: dict = None) -> tuple[Path, str]:
    state_dir, round_id = setup_round_with_artifact(tmp_path, artifact_data)
    generate_round_review(state_dir, round_id)
    return state_dir, round_id


def setup_round_with_proposal(tmp_path: Path, artifact_data: dict = None) -> tuple[Path, str]:
    state_dir, round_id = setup_round_with_review(tmp_path, artifact_data)
    generate_round_proposal(state_dir, round_id)
    return state_dir, round_id


# ---------------------------------------------------------------------------
# Round-scoped review
# ---------------------------------------------------------------------------

class TestGenerateRoundReview:
    def test_review_packet_written_to_round_dir(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        _, saved = generate_round_review(state_dir, round_id)
        assert saved.exists()
        assert saved.name == "review_packet.json"
        round_dir = state_dir / "rounds" / round_id
        assert saved.parent == round_dir

    def test_review_packet_is_valid_json(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        _, saved = generate_round_review(state_dir, round_id)
        data = json.loads(saved.read_text())
        assert "category" not in data  # not an escalation packet
        assert "run_summary" in data

    def test_review_reflects_round_artifact_status(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        packet, _ = generate_round_review(state_dir, round_id)
        assert packet.run_summary.status == "partial"

    def test_review_reflects_round_artifact_unresolved(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        packet, _ = generate_round_review(state_dir, round_id)
        assert "test_edge failing" in packet.run_summary.unresolved_items

    def test_review_reflects_project_phase(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        packet, _ = generate_round_review(state_dir, round_id)
        assert packet.current_phase == "Phase 10"

    def test_missing_round_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        with pytest.raises(RoundError, match="does not exist"):
            generate_round_review(state_dir, "round-0099")

    def test_missing_run_artifact_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        with pytest.raises(RoundError, match="run_artifact.json"):
            generate_round_review(state_dir, r.round_id)

    def test_source_of_truth_unchanged(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        before_ws = (state_dir / "working_state.yaml").read_text()
        before_dl = (state_dir / "decision_log.yaml").read_text()
        before_ch = (state_dir / "project_charter.md").read_text()
        generate_round_review(state_dir, round_id)
        assert (state_dir / "working_state.yaml").read_text() == before_ws
        assert (state_dir / "decision_log.yaml").read_text() == before_dl
        assert (state_dir / "project_charter.md").read_text() == before_ch

    def test_deterministic_content(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        p1, _ = generate_round_review(state_dir, round_id)
        p2, _ = generate_round_review(state_dir, round_id)
        assert p1.current_phase == p2.current_phase
        assert p1.run_summary.status == p2.run_summary.status
        assert p1.run_summary.unresolved_items == p2.run_summary.unresolved_items


# ---------------------------------------------------------------------------
# Round-scoped proposal
# ---------------------------------------------------------------------------

class TestGenerateRoundProposal:
    def test_proposal_written_to_round_dir(self, tmp_path):
        state_dir, round_id = setup_round_with_review(tmp_path)
        _, saved = generate_round_proposal(state_dir, round_id)
        assert saved.exists()
        assert saved.name == "state_update_proposal.json"
        round_dir = state_dir / "rounds" / round_id
        assert saved.parent == round_dir

    def test_proposal_is_valid_json(self, tmp_path):
        state_dir, round_id = setup_round_with_review(tmp_path)
        _, saved = generate_round_proposal(state_dir, round_id)
        data = json.loads(saved.read_text())
        assert "proposed_recent_progress_additions" in data
        assert "project_name" in data

    def test_proposal_reflects_round_artifact(self, tmp_path):
        state_dir, round_id = setup_round_with_review(tmp_path)
        proposal, _ = generate_round_proposal(state_dir, round_id)
        assert "Added feature_y()" in proposal.proposed_recent_progress_additions

    def test_missing_round_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        with pytest.raises(RoundError, match="does not exist"):
            generate_round_proposal(state_dir, "round-0099")

    def test_missing_run_artifact_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        with pytest.raises(RoundError, match="run_artifact.json"):
            generate_round_proposal(state_dir, r.round_id)

    def test_missing_review_packet_raises(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        with pytest.raises(RoundError, match="review_packet.json"):
            generate_round_proposal(state_dir, round_id)

    def test_source_of_truth_unchanged(self, tmp_path):
        state_dir, round_id = setup_round_with_review(tmp_path)
        before_ws = (state_dir / "working_state.yaml").read_text()
        before_dl = (state_dir / "decision_log.yaml").read_text()
        generate_round_proposal(state_dir, round_id)
        assert (state_dir / "working_state.yaml").read_text() == before_ws
        assert (state_dir / "decision_log.yaml").read_text() == before_dl

    def test_proposal_not_applied_automatically(self, tmp_path):
        state_dir, round_id = setup_round_with_review(tmp_path)
        before_ws = (state_dir / "working_state.yaml").read_text()
        generate_round_proposal(state_dir, round_id)
        assert (state_dir / "working_state.yaml").read_text() == before_ws


# ---------------------------------------------------------------------------
# Round-scoped escalation
# ---------------------------------------------------------------------------

class TestGenerateRoundEscalation:
    def test_escalation_written_to_round_dir(self, tmp_path):
        state_dir, round_id = setup_round_with_proposal(tmp_path)
        _, saved = generate_round_escalation(state_dir, round_id)
        assert saved.exists()
        assert saved.name == "escalation_packet.json"
        round_dir = state_dir / "rounds" / round_id
        assert saved.parent == round_dir

    def test_escalation_is_valid_json(self, tmp_path):
        state_dir, round_id = setup_round_with_proposal(tmp_path)
        _, saved = generate_round_escalation(state_dir, round_id)
        data = json.loads(saved.read_text())
        assert "category" in data
        assert "severity" in data
        assert "evidence" in data

    def test_escalation_category_for_partial_run(self, tmp_path):
        state_dir, round_id = setup_round_with_proposal(tmp_path)
        packet, _ = generate_round_escalation(state_dir, round_id)
        assert packet.category != "none"

    def test_escalation_none_for_clean_run(self, tmp_path):
        state_dir, round_id = setup_round_with_proposal(tmp_path, CLEAN_ARTIFACT)
        packet, _ = generate_round_escalation(state_dir, round_id)
        assert packet.category == "none"
        assert packet.severity == "none"

    def test_missing_round_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        with pytest.raises(RoundError, match="does not exist"):
            generate_round_escalation(state_dir, "round-0099")

    def test_missing_run_artifact_raises(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r = start_round(state_dir)
        with pytest.raises(RoundError, match="run_artifact.json"):
            generate_round_escalation(state_dir, r.round_id)

    def test_missing_proposal_raises(self, tmp_path):
        state_dir, round_id = setup_round_with_review(tmp_path)
        with pytest.raises(RoundError, match="state_update_proposal.json"):
            generate_round_escalation(state_dir, round_id)

    def test_source_of_truth_unchanged(self, tmp_path):
        state_dir, round_id = setup_round_with_proposal(tmp_path)
        before_ws = (state_dir / "working_state.yaml").read_text()
        before_dl = (state_dir / "decision_log.yaml").read_text()
        generate_round_escalation(state_dir, round_id)
        assert (state_dir / "working_state.yaml").read_text() == before_ws
        assert (state_dir / "decision_log.yaml").read_text() == before_dl


# ---------------------------------------------------------------------------
# Full round pipeline compatibility
# ---------------------------------------------------------------------------

class TestFullRoundPipeline:
    def test_full_pipeline_produces_all_artifacts(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        round_dir = state_dir / "rounds" / round_id

        generate_round_review(state_dir, round_id)
        generate_round_proposal(state_dir, round_id)
        generate_round_escalation(state_dir, round_id)

        assert (round_dir / "run_artifact.json").exists()
        assert (round_dir / "review_packet.json").exists()
        assert (round_dir / "state_update_proposal.json").exists()
        assert (round_dir / "escalation_packet.json").exists()

    def test_project_level_artifacts_not_polluted(self, tmp_path):
        state_dir, round_id = setup_round_with_artifact(tmp_path)
        generate_round_review(state_dir, round_id)
        generate_round_proposal(state_dir, round_id)
        generate_round_escalation(state_dir, round_id)

        # Project-level artifact files must not be created by round operations
        assert not (state_dir / "review_packet.json").exists()
        assert not (state_dir / "state_update_proposal.json").exists()
        assert not (state_dir / "escalation_packet.json").exists()
