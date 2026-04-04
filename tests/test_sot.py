"""Tests for orch.sot — Source-of-Truth parsing and updates."""
import pytest
from pathlib import Path

from orch.sot import parse_current_phase, mark_task_complete, is_phase_complete, append_decision_entry, _parse_phase_content


SAMPLE_PHASE = """\
# P28: Deterministic Relational Appraisal Expansion

## Phase Goal
Expand deterministic relational appraisal coverage.

## In Scope
- expand T4 coverage

## Out of Scope
- no freeform NLP

## Task Queue
- [ ] P28-T6: Calibrate signal intensity ranges for new output shapes
- [ ] P28-T7: Some future task

## Completed Tasks
- [x] P28-T5: Audit same-day composition safety
- [x] P28-T4: Add comprehensive test coverage

## Current Status
Ready for calibration.
"""

SAMPLE_PHASE_ALL_DONE = """\
# P28: Expansion

## Phase Goal
Expand stuff.

## Task Queue
- [x] P28-T1: Done task

## Completed Tasks
- [x] P28-T1: Done task
"""


class TestParseCurrentPhase:
    def test_extracts_phase_id(self):
        info = _parse_phase_content(SAMPLE_PHASE)
        assert info.phase_id == "P28"

    def test_extracts_phase_title(self):
        info = _parse_phase_content(SAMPLE_PHASE)
        assert "Deterministic" in info.phase_title

    def test_extracts_phase_goal(self):
        info = _parse_phase_content(SAMPLE_PHASE)
        assert "relational appraisal" in info.phase_goal.lower()

    def test_finds_first_unfinished_task(self):
        info = _parse_phase_content(SAMPLE_PHASE)
        assert info.next_task_key == "P28-T6"
        assert "Calibrate" in info.next_task_desc

    def test_not_all_done(self):
        info = _parse_phase_content(SAMPLE_PHASE)
        assert info.all_done is False

    def test_all_done_when_no_unchecked(self):
        info = _parse_phase_content(SAMPLE_PHASE_ALL_DONE)
        assert info.all_done is True
        assert info.next_task_key == ""

    def test_missing_file(self, tmp_path):
        info = parse_current_phase(tmp_path)
        assert info.phase_id == ""
        assert info.all_done is True

    def test_from_file(self, tmp_path):
        (tmp_path / "current_phase.md").write_text(SAMPLE_PHASE)
        info = parse_current_phase(tmp_path)
        assert info.next_task_key == "P28-T6"


class TestMarkTaskComplete:
    def test_marks_task(self, tmp_path):
        (tmp_path / "current_phase.md").write_text(SAMPLE_PHASE)
        result = mark_task_complete(tmp_path, "P28-T6", "Round round-0028")
        assert result is True

        content = (tmp_path / "current_phase.md").read_text()
        assert "- [x] P28-T6:" in content
        assert "Round round-0028" in content
        # P28-T7 should still be unchecked
        assert "- [ ] P28-T7:" in content

    def test_marks_without_note(self, tmp_path):
        (tmp_path / "current_phase.md").write_text(SAMPLE_PHASE)
        mark_task_complete(tmp_path, "P28-T6")
        content = (tmp_path / "current_phase.md").read_text()
        assert "- [x] P28-T6: Calibrate signal intensity" in content

    def test_nonexistent_task(self, tmp_path):
        (tmp_path / "current_phase.md").write_text(SAMPLE_PHASE)
        result = mark_task_complete(tmp_path, "P99-T99")
        assert result is False

    def test_already_complete_not_changed(self, tmp_path):
        (tmp_path / "current_phase.md").write_text(SAMPLE_PHASE)
        # P28-T5 is already complete
        result = mark_task_complete(tmp_path, "P28-T5")
        assert result is False

    def test_phase_complete_after_marking_last(self, tmp_path):
        phase = """\
# P1: Test

## Task Queue
- [ ] P1-T1: Only task

## Completed Tasks
(none)
"""
        (tmp_path / "current_phase.md").write_text(phase)
        assert not is_phase_complete(tmp_path)

        mark_task_complete(tmp_path, "P1-T1")
        assert is_phase_complete(tmp_path)


class TestIsPhaseComplete:
    def test_incomplete(self, tmp_path):
        (tmp_path / "current_phase.md").write_text(SAMPLE_PHASE)
        assert not is_phase_complete(tmp_path)

    def test_complete(self, tmp_path):
        (tmp_path / "current_phase.md").write_text(SAMPLE_PHASE_ALL_DONE)
        assert is_phase_complete(tmp_path)

    def test_missing_file(self, tmp_path):
        # No file means "all done" (nothing to do)
        assert is_phase_complete(tmp_path)


class TestAppendDecisionEntry:
    def _setup_decisions(self, tmp_path):
        (tmp_path / "decisions.md").write_text(
            "# Decisions\n\n## 2026-01-01 — Old decision\n**Decision:** something\n"
        )

    def test_appends_on_pass(self, tmp_path):
        """decisions.md must be updated when append_decision_entry is called."""
        self._setup_decisions(tmp_path)
        result = append_decision_entry(
            tmp_path,
            round_id="round-0028",
            phase_id="P28",
            task_key="P28-T6",
            task_title="Calibrate signal ranges",
            outcome_summary="Calibrated intensity bounds for patterns A/B",
            hard_gate_summary="all passed",
            notes="34 tests pass",
        )
        assert result is True

        content = (tmp_path / "decisions.md").read_text()
        assert "round-0028" in content
        assert "P28-T6" in content
        assert "Calibrate signal ranges" in content
        assert "all passed" in content
        assert "34 tests pass" in content
        # Old content preserved
        assert "Old decision" in content

    def test_preserves_existing_content(self, tmp_path):
        """Append-only: existing entries must not be modified."""
        self._setup_decisions(tmp_path)
        original = (tmp_path / "decisions.md").read_text()

        append_decision_entry(
            tmp_path,
            round_id="round-0028",
            phase_id="P28",
            task_key="P28-T6",
            task_title="Task",
            outcome_summary="Done",
        )
        content = (tmp_path / "decisions.md").read_text()
        # Original content must appear before the new entry
        assert content.startswith(original.rstrip())

    def test_does_not_append_when_no_decisions_file(self, tmp_path):
        """If decisions.md doesn't exist, return False and don't create it."""
        result = append_decision_entry(
            tmp_path,
            round_id="round-0001",
            phase_id="P1",
            task_key="P1-T1",
            task_title="Task",
            outcome_summary="Done",
        )
        assert result is False
        assert not (tmp_path / "decisions.md").exists()

    def test_entry_has_structured_format(self, tmp_path):
        """Entry must contain date, round_id, phase_id, task_key, outcome."""
        self._setup_decisions(tmp_path)
        append_decision_entry(
            tmp_path,
            round_id="round-0005",
            phase_id="P10",
            task_key="P10-T3",
            task_title="Implement feature X",
            outcome_summary="Feature X implemented",
        )
        content = (tmp_path / "decisions.md").read_text()
        # Must have ## heading with date format
        assert "## 20" in content  # Date starts with year 20xx
        assert "P10" in content
        assert "P10-T3" in content
        assert "Feature X implemented" in content
