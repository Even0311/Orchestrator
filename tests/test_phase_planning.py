"""Tests for phase planning — roadmap extraction, status management, prompt building."""
import pytest
from pathlib import Path

from orch.sot import (
    extract_next_phase_from_roadmap,
    get_phase_status,
    set_phase_status,
    _split_h2_sections,
    _extract_h3_section,
)
from orch.engine.phase_planner import _build_planning_prompt, _parse_task_lines


SAMPLE_ROADMAP = """\
# Phase Roadmap

## Phase 28 — Deterministic Relational Appraisal Expansion

### Goal
Expand deterministic relational appraisal coverage.

### In Scope
- carefully expand event-aware relational appraisal conditions
- allow more than one narrow approved path

### Out of Scope
- no freeform natural-language appraisal
- no live LLM runtime

### Exit Condition
- T4 has limited but real coverage

## Phase 29 — Appraisal / Settlement Boundary Extraction

### Goal
Make the appraisal layer an explicit seam in the architecture.

### In Scope
- extract or formalize appraisal-facing input schema
- input schema must accommodate all 8 tick types
- formalize appraisal output contract

### Out of Scope
- no production LLM integration yet
- no prompt experimentation

### Exit Condition
- appraisal boundary is explicit

## Phase 30 — Offline / Shadow LLM Appraisal Validation

### Goal
Validate LLM appraisal against the extracted seam.

### In Scope
- run shadow appraisal comparisons

### Out of Scope
- no full production control handoff
"""


class TestExtractNextPhase:
    def test_finds_next_phase(self):
        result = extract_next_phase_from_roadmap(SAMPLE_ROADMAP, "P28")
        assert result is not None
        assert result["phase_id"] == "P29"
        assert "Appraisal" in result["title"]
        assert "explicit seam" in result["goal"]
        assert "8 tick types" in result["in_scope"]
        assert "no production LLM" in result["out_of_scope"]

    def test_finds_p30_after_p29(self):
        result = extract_next_phase_from_roadmap(SAMPLE_ROADMAP, "P29")
        assert result is not None
        assert result["phase_id"] == "P30"

    def test_returns_none_for_last_phase(self):
        result = extract_next_phase_from_roadmap(SAMPLE_ROADMAP, "P30")
        assert result is None

    def test_returns_none_for_unknown_phase(self):
        result = extract_next_phase_from_roadmap(SAMPLE_ROADMAP, "P99")
        assert result is None

    def test_phase_id_format(self):
        result = extract_next_phase_from_roadmap(SAMPLE_ROADMAP, "P28")
        assert result["phase_id"] == "P29"
        assert result["title"].startswith("P29:")


class TestSplitH2Sections:
    def test_splits_sections(self):
        sections = _split_h2_sections(SAMPLE_ROADMAP)
        assert len(sections) == 3
        assert "Phase 28" in sections[0][0]
        assert "Phase 29" in sections[1][0]

    def test_empty_text(self):
        assert _split_h2_sections("") == []


class TestExtractH3Section:
    def test_extracts_goal(self):
        body = "### Goal\nDo something.\n\n### In Scope\n- item"
        result = _extract_h3_section(body, "Goal")
        assert result == "Do something."

    def test_extracts_in_scope(self):
        body = "### Goal\nDo something.\n\n### In Scope\n- item 1\n- item 2\n\n### Out of Scope\n- no"
        result = _extract_h3_section(body, "In Scope")
        assert "item 1" in result
        assert "item 2" in result

    def test_missing_section(self):
        result = _extract_h3_section("### Goal\nstuff", "Missing")
        assert result == ""


class TestPhaseStatus:
    def test_get_status_draft(self, tmp_path):
        (tmp_path / "current_phase.md").write_text("# P29: Test\n<!-- status: draft -->\n\n## Phase Goal\nGoal")
        assert get_phase_status(tmp_path) == "draft"

    def test_get_status_approved(self, tmp_path):
        (tmp_path / "current_phase.md").write_text("# P29: Test\n<!-- status: approved -->\n\n## Phase Goal\nGoal")
        assert get_phase_status(tmp_path) == "approved"

    def test_get_status_legacy(self, tmp_path):
        (tmp_path / "current_phase.md").write_text("# P28: Test\n\n## Phase Goal\nGoal")
        assert get_phase_status(tmp_path) == ""

    def test_get_status_missing_file(self, tmp_path):
        assert get_phase_status(tmp_path) == ""

    def test_set_status_insert(self, tmp_path):
        (tmp_path / "current_phase.md").write_text("# P29: Test\n\n## Phase Goal\nGoal")
        set_phase_status(tmp_path, "draft")
        assert get_phase_status(tmp_path) == "draft"

    def test_set_status_update(self, tmp_path):
        (tmp_path / "current_phase.md").write_text("# P29: Test\n<!-- status: draft -->\n\n## Phase Goal\nGoal")
        set_phase_status(tmp_path, "approved")
        assert get_phase_status(tmp_path) == "approved"
        content = (tmp_path / "current_phase.md").read_text()
        assert "draft" not in content


class TestParseTaskLines:
    def test_parses_standard_lines(self):
        output = "- [ ] P29-T1: Extract appraisal input schema\n- [ ] P29-T2: Define output contract\n"
        lines = _parse_task_lines(output, "P29")
        assert len(lines) == 2
        assert "P29-T1" in lines[0]

    def test_ignores_non_task_lines(self):
        output = "Here are the tasks:\n\n- [ ] P29-T1: Do stuff\n\nThese are ordered.\n"
        lines = _parse_task_lines(output, "P29")
        assert len(lines) == 1

    def test_empty_output(self):
        assert _parse_task_lines("", "P29") == []

    def test_fallback_without_phase_id(self):
        output = "- [ ] T1: Generic task\n"
        lines = _parse_task_lines(output, "P29")
        # Falls through to fallback
        assert len(lines) == 1


class TestBuildPlanningPrompt:
    def test_includes_all_sections(self):
        prompt = _build_planning_prompt(
            next_phase={
                "phase_id": "P29",
                "title": "P29: Boundary Extraction",
                "goal": "Make boundary explicit",
                "in_scope": "- extract schema",
                "out_of_scope": "- no LLM yet",
            },
            completed_phase_md="# P28\n- [x] P28-T6: Done",
            decisions_md="## 2026-04-04 — Some decision",
            vision_md="# Vision\nBuild a simulation.",
        )
        assert "P29" in prompt
        assert "Boundary Extraction" in prompt
        assert "Make boundary explicit" in prompt
        assert "extract schema" in prompt
        assert "no LLM yet" in prompt
        assert "P28" in prompt
        assert "simulation" in prompt
        assert "- [ ] P29-T{n}" in prompt
