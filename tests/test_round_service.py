"""Tests for Phase 8 round workspace / round state model."""
import json
from pathlib import Path

import pytest

from src.services.round_service import (
    start_round,
    RoundError,
    RoundStartResult,
    _next_round_id,
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

CHARTER = """\
# Project Charter

## 项目概述
A test project for orchestration.

## Out of Scope
- Do not modify the database schema
- Do not change the public API
"""


def setup_project(tmp_path: Path) -> Path:
    state_dir = tmp_path / "projects" / "test-project"
    state_dir.mkdir(parents=True)
    (state_dir / "working_state.yaml").write_text(WORKING_STATE_YAML, encoding="utf-8")
    (state_dir / "decision_log.yaml").write_text("decisions: []\n", encoding="utf-8")
    (state_dir / "project_charter.md").write_text(CHARTER, encoding="utf-8")
    return state_dir


# ---------------------------------------------------------------------------
# _next_round_id
# ---------------------------------------------------------------------------

class TestNextRoundId:
    def test_first_round_when_no_dir(self, tmp_path):
        rounds_dir = tmp_path / "rounds"
        assert _next_round_id(rounds_dir) == "round-0001"

    def test_first_round_when_dir_empty(self, tmp_path):
        rounds_dir = tmp_path / "rounds"
        rounds_dir.mkdir()
        assert _next_round_id(rounds_dir) == "round-0001"

    def test_increments_from_existing(self, tmp_path):
        rounds_dir = tmp_path / "rounds"
        (rounds_dir / "round-0001").mkdir(parents=True)
        assert _next_round_id(rounds_dir) == "round-0002"

    def test_increments_from_highest(self, tmp_path):
        rounds_dir = tmp_path / "rounds"
        rounds_dir.mkdir()
        for name in ("round-0001", "round-0003", "round-0002"):
            (rounds_dir / name).mkdir()
        assert _next_round_id(rounds_dir) == "round-0004"

    def test_ignores_non_round_dirs(self, tmp_path):
        rounds_dir = tmp_path / "rounds"
        rounds_dir.mkdir()
        (rounds_dir / "round-0001").mkdir()
        (rounds_dir / "other-dir").mkdir()
        (rounds_dir / "not-a-dir.txt").write_text("x")
        assert _next_round_id(rounds_dir) == "round-0002"


# ---------------------------------------------------------------------------
# start_round — structure
# ---------------------------------------------------------------------------

class TestRoundDirectory:
    def test_round_dir_created_under_rounds(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        assert result.round_dir.exists()
        assert result.round_dir.parent.name == "rounds"
        assert result.round_dir.parent.parent == state_dir

    def test_round_id_is_round_0001_first_time(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        assert result.round_id == "round-0001"

    def test_repeated_start_increments_id(self, tmp_path):
        state_dir = setup_project(tmp_path)
        r1 = start_round(state_dir)
        r2 = start_round(state_dir)
        assert r1.round_id == "round-0001"
        assert r2.round_id == "round-0002"

    def test_round_dir_name_matches_round_id(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        assert result.round_dir.name == result.round_id


# ---------------------------------------------------------------------------
# start_round — round_state.json
# ---------------------------------------------------------------------------

class TestRoundStateFile:
    def test_round_state_file_exists(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        assert result.round_state_path.exists()
        assert result.round_state_path.name == "round_state.json"

    def test_round_state_is_valid_json(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        data = json.loads(result.round_state_path.read_text())
        assert isinstance(data, dict)

    def test_round_state_required_fields(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        data = json.loads(result.round_state_path.read_text())
        for field in ("round_id", "project_name", "created_at", "status",
                      "source_task_role", "based_on_phase", "based_on_goal"):
            assert field in data, f"Missing field: {field}"

    def test_round_state_status_is_task_ready(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        data = json.loads(result.round_state_path.read_text())
        assert data["status"] == "task_ready"

    def test_round_state_role_is_claude(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        data = json.loads(result.round_state_path.read_text())
        assert data["source_task_role"] == "claude"

    def test_round_state_reflects_project_state(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        data = json.loads(result.round_state_path.read_text())
        assert data["project_name"] == "test-project"
        assert data["based_on_phase"] == "Phase 10"
        assert "Implement feature Y" in data["based_on_goal"]


# ---------------------------------------------------------------------------
# start_round — task_packet_claude.json
# ---------------------------------------------------------------------------

class TestTaskPacketFile:
    def test_task_packet_file_exists(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        assert result.task_packet_path.exists()
        assert result.task_packet_path.name == "task_packet_claude.json"

    def test_task_packet_is_valid_json(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        data = json.loads(result.task_packet_path.read_text())
        assert data["role"] == "claude"
        assert data["project_name"] == "test-project"

    def test_task_packet_contains_phase_and_goal(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        data = json.loads(result.task_packet_path.read_text())
        assert data["current_phase"] == "Phase 10"
        assert "Implement feature Y" in data["current_goal"]


# ---------------------------------------------------------------------------
# start_round — task_for_claude.md
# ---------------------------------------------------------------------------

class TestTaskFile:
    def test_task_file_exists(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        assert result.task_file_path.exists()
        assert result.task_file_path.name == "task_for_claude.md"

    def test_task_file_contains_round_id(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        content = result.task_file_path.read_text()
        assert result.round_id in content

    def test_task_file_contains_phase(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        content = result.task_file_path.read_text()
        assert "Phase 10" in content

    def test_task_file_contains_goal(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        content = result.task_file_path.read_text()
        assert "Implement feature Y" in content

    def test_task_file_contains_next_step(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        content = result.task_file_path.read_text()
        assert "Run integration tests" in content

    def test_task_file_contains_implementation_boundaries(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        content = result.task_file_path.read_text()
        assert "Do not modify the database schema" in content

    def test_task_file_contains_return_contract_section(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        content = result.task_file_path.read_text()
        assert "Return Contract" in content
        assert "unresolved_items" in content

    def test_task_file_contains_json_rules(self, tmp_path):
        state_dir = setup_project(tmp_path)
        result = start_round(state_dir)
        content = result.task_file_path.read_text()
        assert "status" in content
        assert "json" in content.lower()


# ---------------------------------------------------------------------------
# Source-of-truth immutability
# ---------------------------------------------------------------------------

class TestSourceOfTruthUnchanged:
    def test_working_state_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "working_state.yaml").read_text()
        start_round(state_dir)
        assert (state_dir / "working_state.yaml").read_text() == before

    def test_decision_log_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "decision_log.yaml").read_text()
        start_round(state_dir)
        assert (state_dir / "decision_log.yaml").read_text() == before

    def test_charter_not_modified(self, tmp_path):
        state_dir = setup_project(tmp_path)
        before = (state_dir / "project_charter.md").read_text()
        start_round(state_dir)
        assert (state_dir / "project_charter.md").read_text() == before
