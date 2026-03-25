"""Tests for Phase 7 approved update application."""
import json
from pathlib import Path

import pytest
import yaml

from src.services.apply_service import (
    apply_approved_update,
    ApplyError,
    _extract_risk_description,
    _derive_decision_title,
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


def setup_project(tmp_path: Path, proposal_data: dict = None) -> tuple[Path, Path]:
    state_dir = tmp_path / "projects" / "test-project"
    state_dir.mkdir(parents=True)
    (state_dir / "working_state.yaml").write_text(WORKING_STATE_YAML, encoding="utf-8")
    (state_dir / "decision_log.yaml").write_text("decisions: []\n", encoding="utf-8")
    (state_dir / "project_charter.md").write_text("# Charter\n\nOverview.\n", encoding="utf-8")

    proposal = proposal_data or PROPOSAL_BASE
    proposal_path = state_dir / "state_update_proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    return state_dir, proposal_path


# ---------------------------------------------------------------------------
# working_state.yaml application
# ---------------------------------------------------------------------------

class TestApplyWorkingState:
    def test_progress_additions_appended(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Did thing X", "Did thing Y"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        items = [p["item"] for p in data["recent_progress"]]
        assert "Did thing X" in items
        assert "Did thing Y" in items

    def test_progress_additions_marked_completed(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Did thing X"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        new_item = next(p for p in data["recent_progress"] if p["item"] == "Did thing X")
        assert new_item["completed"] is True

    def test_existing_progress_preserved(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Did thing X"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        items = [p["item"] for p in data["recent_progress"]]
        assert "Task A" in items

    def test_goal_update_applied(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_current_goal_update": "New goal.",
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        assert data["current_goal"] == "New goal."

    def test_next_step_update_applied(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_next_expected_step_update": "Run tests.",
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        assert data["next_expected_step"] == "Run tests."

    def test_risk_updates_appended(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_risk_updates": ["[NEW RISK CANDIDATE] Unresolved: test_edge failing"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        descriptions = [r["description"] for r in data["current_risks"]]
        assert "Unresolved: test_edge failing" in descriptions

    def test_risk_prefix_stripped(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_risk_updates": ["[NEW RISK CANDIDATE] Something bad"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        descriptions = [r["description"] for r in data["current_risks"]]
        assert not any("[NEW RISK CANDIDATE]" in d for d in descriptions)

    def test_risk_severity_defaults_to_medium(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_risk_updates": ["Some risk"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        new_risk = next(r for r in data["current_risks"] if r["description"] == "Some risk")
        assert new_risk["severity"] == "medium"

    def test_existing_risks_preserved(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_risk_updates": ["New risk"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "working_state.yaml").read_text())
        descriptions = [r["description"] for r in data["current_risks"]]
        assert "Known risk" in descriptions

    def test_working_state_modified_flag(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Done X"],
        })
        result = apply_approved_update(state_dir, proposal_path)
        assert result.working_state_modified


# ---------------------------------------------------------------------------
# decision_log.yaml application
# ---------------------------------------------------------------------------

class TestApplyDecisionLog:
    def test_candidates_appended(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_decision_log_candidates": [
                "Consider documenting: implementation approach for Phase 10 — what was decided."
            ],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "decision_log.yaml").read_text())
        assert len(data["decisions"]) == 1

    def test_multiple_candidates_all_appended(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_decision_log_candidates": ["Candidate A", "Candidate B"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "decision_log.yaml").read_text())
        assert len(data["decisions"]) == 2

    def test_entry_has_required_fields(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_decision_log_candidates": ["Some decision"],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "decision_log.yaml").read_text())
        entry = data["decisions"][0]
        assert "date" in entry
        assert "title" in entry
        assert "decision" in entry
        assert "rationale" in entry

    def test_decision_field_contains_full_candidate(self, tmp_path):
        candidate = "Consider documenting: some approach — details here."
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_decision_log_candidates": [candidate],
        })
        apply_approved_update(state_dir, proposal_path)
        data = yaml.safe_load((state_dir / "decision_log.yaml").read_text())
        assert data["decisions"][0]["decision"] == candidate

    def test_decision_log_modified_flag(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_decision_log_candidates": ["Candidate"],
        })
        result = apply_approved_update(state_dir, proposal_path)
        assert result.decision_log_modified


# ---------------------------------------------------------------------------
# Combined application
# ---------------------------------------------------------------------------

class TestApplyCombined:
    def test_working_state_and_decision_log_both_updated(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Feature added"],
            "proposed_current_goal_update": "Next phase goal.",
            "proposed_decision_log_candidates": ["Consider documenting: approach"],
        })
        result = apply_approved_update(state_dir, proposal_path)
        assert result.working_state_modified
        assert result.decision_log_modified
        assert len(result.sections_applied) >= 2
        assert len(result.backup_paths) >= 2


# ---------------------------------------------------------------------------
# No-op behavior
# ---------------------------------------------------------------------------

class TestNoOp:
    def test_empty_proposal_is_noop(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path)
        result = apply_approved_update(state_dir, proposal_path)
        assert result.no_op
        assert result.sections_applied == []
        assert result.backup_paths == []

    def test_noop_does_not_modify_working_state(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path)
        before = (state_dir / "working_state.yaml").read_text()
        apply_approved_update(state_dir, proposal_path)
        assert (state_dir / "working_state.yaml").read_text() == before

    def test_noop_does_not_modify_decision_log(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path)
        before = (state_dir / "decision_log.yaml").read_text()
        apply_approved_update(state_dir, proposal_path)
        assert (state_dir / "decision_log.yaml").read_text() == before


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    def test_project_mismatch_raises(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "project_name": "different-project",
        })
        with pytest.raises(ApplyError, match="mismatch"):
            apply_approved_update(state_dir, proposal_path)

    def test_missing_proposal_raises(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        with pytest.raises(ApplyError, match="not found"):
            apply_approved_update(state_dir, state_dir / "nonexistent.json")

    def test_invalid_json_raises(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path)
        proposal_path.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ApplyError):
            apply_approved_update(state_dir, proposal_path)

    def test_invalid_proposal_schema_raises(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path)
        proposal_path.write_text(json.dumps({"project_name": "test-project"}), encoding="utf-8")
        with pytest.raises(ApplyError):
            apply_approved_update(state_dir, proposal_path)


# ---------------------------------------------------------------------------
# Backup behavior
# ---------------------------------------------------------------------------

class TestBackups:
    def test_backup_created_for_working_state(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Done X"],
        })
        result = apply_approved_update(state_dir, proposal_path)
        assert any("working_state" in str(bp) for bp in result.backup_paths)
        assert all(bp.exists() for bp in result.backup_paths)

    def test_backup_created_for_decision_log(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_decision_log_candidates": ["Candidate"],
        })
        result = apply_approved_update(state_dir, proposal_path)
        assert any("decision_log" in str(bp) for bp in result.backup_paths)

    def test_no_backup_on_noop(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path)
        result = apply_approved_update(state_dir, proposal_path)
        assert result.backup_paths == []

    def test_backups_stored_in_backups_dir(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Done X"],
        })
        result = apply_approved_update(state_dir, proposal_path)
        assert all(
            "backups" in str(bp) for bp in result.backup_paths
        )
        assert (state_dir / "backups").is_dir()

    def test_backup_content_matches_original(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Done X"],
        })
        original = (state_dir / "working_state.yaml").read_text()
        result = apply_approved_update(state_dir, proposal_path)
        ws_backup = next(bp for bp in result.backup_paths if "working_state" in str(bp))
        assert ws_backup.read_text() == original


# ---------------------------------------------------------------------------
# project_charter.md must not be modified
# ---------------------------------------------------------------------------

class TestCharterUnchanged:
    def test_charter_not_modified_by_full_proposal(self, tmp_path):
        state_dir, proposal_path = setup_project(tmp_path, {
            **PROPOSAL_BASE,
            "proposed_recent_progress_additions": ["Done X"],
            "proposed_current_goal_update": "New goal.",
            "proposed_next_expected_step_update": "Next step.",
            "proposed_risk_updates": ["New risk"],
            "proposed_decision_log_candidates": ["Candidate"],
        })
        before = (state_dir / "project_charter.md").read_text()
        apply_approved_update(state_dir, proposal_path)
        assert (state_dir / "project_charter.md").read_text() == before


# ---------------------------------------------------------------------------
# Helper unit tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_extract_risk_description_strips_prefix(self):
        assert _extract_risk_description("[NEW RISK CANDIDATE] Something") == "Something"

    def test_extract_risk_description_passthrough(self):
        assert _extract_risk_description("Plain risk") == "Plain risk"

    def test_derive_decision_title_strips_consider_prefix(self):
        candidate = "Consider documenting: implementation approach for Phase 10 — details."
        title = _derive_decision_title(candidate)
        assert "implementation approach" in title
        assert "Consider documenting" not in title

    def test_derive_decision_title_respects_max_length(self):
        candidate = "Consider documenting: " + "word " * 30
        title = _derive_decision_title(candidate)
        assert len(title) <= 70
