"""Tests for role-specific task packet generation."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models import TaskPacket, SUPPORTED_ROLES
from src.models.working_state import WorkingState, Risk, Progress
from src.models.decision_log import DecisionLog, DecisionEntry
from src.services.task_packet_service import (
    generate_task_packet,
    _build_claude_packet,
    _build_reviewer_packet,
    _build_decision_maker_packet,
)
from src.services.file_reader import FileReader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_state(**overrides) -> WorkingState:
    defaults = dict(
        project_name="TestProject",
        current_phase="Phase 1",
        current_goal="Implement feature X.\n",
        next_expected_step="Run tests and verify output.\n",
        context_notes="Background context here.\n",
        recent_progress=[
            Progress(item="Task A", completed=True),
            Progress(item="Task B", completed=False),
        ],
        current_risks=[
            Risk(description="Risk alpha", severity="high", mitigation="Mitigate alpha"),
            Risk(description="Risk beta", severity="medium", mitigation="Mitigate beta"),
            Risk(description="Risk gamma", severity="low", mitigation="Mitigate gamma"),
        ],
    )
    defaults.update(overrides)
    return WorkingState(**defaults)


def make_log(n: int = 4) -> DecisionLog:
    decisions = [
        DecisionEntry(
            date=f"2026-03-{i:02d}",
            title=f"Decision {i}",
            decision=f"We decided {i}.\n",
            rationale=f"Because {i}.",
        )
        for i in range(1, n + 1)
    ]
    return DecisionLog(decisions=decisions)


CHARTER = """\
# Charter

## 项目概述

This is a test project overview.

---

## Core Principles

- **Principle one**: Keep it simple.
- **Principle two**: Stay deterministic.

---

## Out of Scope

- No dashboard.
- No LLM in settlement.
"""

NOW = "2026-03-23T00:00:00+00:00"


def make_reader() -> FileReader:
    with patch.object(Path, "exists", return_value=True):
        return FileReader("/fake")


# ---------------------------------------------------------------------------
# SUPPORTED_ROLES
# ---------------------------------------------------------------------------

class TestSupportedRoles:
    def test_contains_all_three(self):
        assert SUPPORTED_ROLES == {"claude", "reviewer", "decision_maker"}


# ---------------------------------------------------------------------------
# Claude packet
# ---------------------------------------------------------------------------

class TestClaudePacket:
    def setup_method(self):
        self.state = make_state()
        self.log = make_log()
        self.reader = make_reader()

    def test_role_is_claude(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.role == "claude"

    def test_has_next_expected_step(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.next_expected_step is not None
        assert packet.next_expected_step == "Run tests and verify output."

    def test_has_implementation_boundaries(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.implementation_boundaries is not None
        assert len(packet.implementation_boundaries) == 2

    def test_has_risks(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.current_risks is not None

    def test_has_recent_progress(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.recent_progress is not None

    def test_has_recent_decisions(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.recent_decisions is not None

    def test_no_project_summary(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.project_summary is None

    def test_no_decision_maker_fields(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.decision_needed is None
        assert packet.why_now is None

    def test_trailing_whitespace_stripped(self):
        packet = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert not packet.current_goal.endswith("\n")
        assert not packet.next_expected_step.endswith("\n")
        assert not packet.context_notes.endswith("\n")


# ---------------------------------------------------------------------------
# Reviewer packet
# ---------------------------------------------------------------------------

class TestReviewerPacket:
    def setup_method(self):
        self.state = make_state()
        self.log = make_log()
        self.reader = make_reader()

    def test_role_is_reviewer(self):
        packet = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.role == "reviewer"

    def test_has_project_summary(self):
        packet = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.project_summary is not None
        assert "test project" in packet.project_summary

    def test_has_inspect_next(self):
        packet = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.inspect_next == "Run tests and verify output."

    def test_has_progress_and_risks_and_decisions(self):
        packet = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.recent_progress is not None
        assert packet.current_risks is not None
        assert packet.recent_decisions is not None

    def test_no_implementation_boundaries(self):
        packet = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.implementation_boundaries is None

    def test_no_decision_maker_fields(self):
        packet = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.decision_needed is None
        assert packet.why_now is None

    def test_no_next_expected_step(self):
        # reviewer uses inspect_next instead
        packet = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.next_expected_step is None


# ---------------------------------------------------------------------------
# Decision-maker packet
# ---------------------------------------------------------------------------

class TestDecisionMakerPacket:
    def setup_method(self):
        self.state = make_state()
        self.log = make_log()
        self.reader = make_reader()

    def test_role_is_decision_maker(self):
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.role == "decision_maker"

    def test_has_decision_needed(self):
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.decision_needed is not None
        assert "Run tests" in packet.decision_needed

    def test_has_why_now(self):
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.why_now == "Background context here."

    def test_risks_sorted_high_first(self):
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.current_risks[0].severity == "high"
        assert packet.current_risks[1].severity == "medium"

    def test_risks_capped_at_top_3(self):
        state = make_state(current_risks=[
            Risk(description=f"Risk {i}", severity=s)
            for i, s in enumerate(["low", "low", "low", "medium", "high"])
        ])
        packet = _build_decision_maker_packet(NOW, CHARTER, state, self.log, self.reader)
        assert len(packet.current_risks) <= 3

    def test_decisions_capped_at_3(self):
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, make_log(6), self.reader)
        assert len(packet.recent_decisions) == 3

    def test_no_project_summary(self):
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.project_summary is None

    def test_no_progress(self):
        # decision_maker does not need full progress list
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.recent_progress is None

    def test_no_implementation_boundaries(self):
        packet = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)
        assert packet.implementation_boundaries is None


# ---------------------------------------------------------------------------
# Role differentiation
# ---------------------------------------------------------------------------

class TestRoleDifferentiation:
    def setup_method(self):
        self.state = make_state()
        self.log = make_log()
        self.reader = make_reader()

    def test_three_roles_produce_different_shapes(self):
        claude = _build_claude_packet(NOW, CHARTER, self.state, self.log, self.reader)
        reviewer = _build_reviewer_packet(NOW, CHARTER, self.state, self.log, self.reader)
        dm = _build_decision_maker_packet(NOW, CHARTER, self.state, self.log, self.reader)

        # Claude has boundaries, others don't
        assert claude.implementation_boundaries is not None
        assert reviewer.implementation_boundaries is None
        assert dm.implementation_boundaries is None

        # Reviewer has project_summary, others don't
        assert reviewer.project_summary is not None
        assert claude.project_summary is None
        assert dm.project_summary is None

        # Decision-maker has decision_needed/why_now, others don't
        assert dm.decision_needed is not None
        assert dm.why_now is not None
        assert claude.decision_needed is None
        assert reviewer.decision_needed is None

    def test_all_share_core_fields(self):
        for role_fn in [_build_claude_packet, _build_reviewer_packet, _build_decision_maker_packet]:
            packet = role_fn(NOW, CHARTER, self.state, self.log, self.reader)
            assert packet.project_name == "TestProject"
            assert packet.current_phase == "Phase 1"
            assert packet.current_goal == "Implement feature X."

    def test_invalid_role_raises(self):
        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ValueError, match="Unsupported role"):
                generate_task_packet(Path("/fake"), "unknown_role")
