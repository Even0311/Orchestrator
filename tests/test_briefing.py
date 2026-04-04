"""Tests for orch.briefing — round brief generation and artifact reading."""
import json
import pytest
from pathlib import Path

from orch.briefing import (
    generate_round_brief,
    read_artifacts,
    write_task_contract,
    _extract_vision_summary,
    _extract_roadmap_context,
)
from orch.models import TaskContract
from orch.sot import PhaseInfo


SAMPLE_VISION = """\
# cyber-community-v2 — Vision

## Project Goal
Build a deterministic social simulation engine with auditable relational appraisal.

## Core Features
- Deterministic tick-based engine
- Relational appraisal signals
- Settlement substrate

## Tech Stack
- Python 3.12, FastAPI, PostgreSQL
- pytest for testing

## Out of Scope
- No freeform NLP
- No live LLM runtime

## Codebase Path
/home/even/projects/cyber-community-v2

## Current Status
### Completed
- MVP backbone
"""

SAMPLE_ROADMAP = """\
# road_map.md

## Purpose
Strategic phase ordering.

## P27: Audit and Stabilization
Audit T4 activation paths, residual behavior, composition safety.

## P28: Deterministic Relational Appraisal Expansion
Expand deterministic relational appraisal beyond single narrow activation.

## P29: Settlement Substrate Enhancement
Improve settlement mechanisms for expanded signal shapes.

## Coarse Outlook
Future phases TBD.
"""


class TestGenerateRoundBrief:
    def _make_phase_info(self):
        return PhaseInfo(
            phase_id="P28",
            phase_title="P28: Expansion",
            phase_goal="Expand coverage",
            next_task_key="P28-T6",
            next_task_desc="Calibrate signal intensity ranges",
            all_done=False,
        )

    def _make_sot_dir(self, tmp_path):
        sot = tmp_path / "sot"
        sot.mkdir()
        (sot / "decisions.md").write_text("# Decisions\n\n## 2026-01-01 — Some decision\n")
        (sot / "vision.md").write_text(SAMPLE_VISION)
        (sot / "road_map.md").write_text(SAMPLE_ROADMAP)
        return sot

    def test_creates_brief_file(self, tmp_path):
        round_dir = tmp_path / "round-0001"
        sot_dir = self._make_sot_dir(tmp_path)

        path = generate_round_brief(
            round_dir=round_dir,
            sot_dir=sot_dir,
            phase_info=self._make_phase_info(),
            round_id="round-0001",
            attempt_num=1,
        )
        assert path.exists()
        content = path.read_text()
        assert "P28-T6" in content
        assert "Calibrate" in content
        assert "round-0001" in content

    def test_includes_vision_context(self, tmp_path):
        """round_brief must include content derived from vision.md."""
        round_dir = tmp_path / "round-0001"
        sot_dir = self._make_sot_dir(tmp_path)

        path = generate_round_brief(
            round_dir=round_dir,
            sot_dir=sot_dir,
            phase_info=self._make_phase_info(),
            round_id="round-0001",
            attempt_num=1,
        )
        content = path.read_text()
        assert "Project Vision Context" in content
        assert "deterministic social simulation" in content
        assert "Python 3.12" in content
        assert "No freeform NLP" in content

    def test_includes_roadmap_context(self, tmp_path):
        """round_brief must include content derived from road_map.md."""
        round_dir = tmp_path / "round-0001"
        sot_dir = self._make_sot_dir(tmp_path)

        path = generate_round_brief(
            round_dir=round_dir,
            sot_dir=sot_dir,
            phase_info=self._make_phase_info(),
            round_id="round-0001",
            attempt_num=1,
        )
        content = path.read_text()
        assert "Roadmap / Phase Context" in content
        assert "P28" in content
        # Should include near-neighbor (P27 or P29)
        assert "P27" in content or "P29" in content

    def test_vision_excludes_codebase_path(self, tmp_path):
        """Vision summary should not include the codebase path section."""
        summary = _extract_vision_summary(SAMPLE_VISION)
        assert "/home/even" not in summary
        assert "Completed" not in summary

    def test_roadmap_extracts_current_phase_context(self):
        """Roadmap context should focus on the current phase section."""
        context = _extract_roadmap_context(SAMPLE_ROADMAP, "P28")
        assert "Deterministic Relational Appraisal Expansion" in context
        # Should include neighbor
        assert "P27" in context or "P29" in context

    def test_roadmap_handles_missing_phase(self):
        """If phase_id not in roadmap, should return some context anyway."""
        context = _extract_roadmap_context(SAMPLE_ROADMAP, "P99")
        # Should still return something (last substantive section)
        assert len(context) > 0

    def test_includes_prior_failure(self, tmp_path):
        round_dir = tmp_path / "round-0001"
        sot_dir = self._make_sot_dir(tmp_path)

        path = generate_round_brief(
            round_dir=round_dir,
            sot_dir=sot_dir,
            phase_info=self._make_phase_info(),
            round_id="round-0001",
            attempt_num=2,
            prior_failure="pytest failed: 3 errors",
        )
        content = path.read_text()
        assert "pytest failed" in content
        assert "Prior Attempt Failed" in content

    def test_includes_recent_rounds(self, tmp_path):
        round_dir = tmp_path / "round-0001"
        sot_dir = self._make_sot_dir(tmp_path)

        path = generate_round_brief(
            round_dir=round_dir,
            sot_dir=sot_dir,
            phase_info=self._make_phase_info(),
            round_id="round-0001",
            attempt_num=1,
            recent_rounds_summary="round-0026 PASSED",
        )
        content = path.read_text()
        assert "round-0026" in content

    def test_without_vision_or_roadmap(self, tmp_path):
        """Brief should still work if vision/roadmap don't exist."""
        round_dir = tmp_path / "round-0001"
        sot_dir = tmp_path / "sot"
        sot_dir.mkdir()

        path = generate_round_brief(
            round_dir=round_dir,
            sot_dir=sot_dir,
            phase_info=self._make_phase_info(),
            round_id="round-0001",
            attempt_num=1,
        )
        content = path.read_text()
        assert "P28-T6" in content
        assert "Project Vision Context" not in content
        assert "Roadmap / Phase Context" not in content


class TestReadArtifacts:
    def test_reads_all_artifacts(self, tmp_path):
        (tmp_path / "task_contract.json").write_text(json.dumps({
            "phase_id": "P28", "task_key": "P28-T6", "title": "t", "objective": "o",
        }))
        (tmp_path / "execution_evidence.json").write_text(json.dumps({
            "summary": "done", "files_changed": ["a.py"],
        }))
        (tmp_path / "review_verdict.json").write_text(json.dumps({
            "verdict": "PASS", "confidence": "high",
        }))

        artifacts = read_artifacts(tmp_path)
        assert artifacts["task_contract"]["task_key"] == "P28-T6"
        assert artifacts["execution_evidence"]["summary"] == "done"
        assert artifacts["review_verdict"]["verdict"] == "PASS"

    def test_missing_artifacts_return_none(self, tmp_path):
        artifacts = read_artifacts(tmp_path)
        assert artifacts["task_contract"] is None
        assert artifacts["execution_evidence"] is None
        assert artifacts["review_verdict"] is None

    def test_malformed_json_returns_none(self, tmp_path):
        (tmp_path / "task_contract.json").write_text("not json")
        artifacts = read_artifacts(tmp_path)
        assert artifacts["task_contract"] is None


class TestWriteTaskContract:
    def test_writes_and_reads_back(self, tmp_path):
        tc = TaskContract(
            phase_id="P28", task_key="P28-T6",
            title="Calibrate", objective="Do calibration",
            allowed_files=["back/**"],
        )
        path = write_task_contract(tmp_path, tc)
        assert path.exists()

        data = json.loads(path.read_text())
        assert data["task_key"] == "P28-T6"
        assert data["allowed_files"] == ["back/**"]
