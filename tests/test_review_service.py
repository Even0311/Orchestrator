"""Tests for review packet generation."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.models import ReviewPacket, ImplementationRunArtifact
from src.models.working_state import WorkingState, Risk, Progress
from src.models.decision_log import DecisionLog, DecisionEntry
from src.services.review_service import (
    generate_review_packet,
    save_review_packet,
    select_latest_artifact,
    _derive_inspect_next,
    ReviewError,
)
from src.services.file_reader import FileReader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CHARTER = """\
# Charter

## 项目概述

Test project overview text.

---

## Core Principles

- **Principle one**: Keep it simple.
"""

WORKING_STATE_YAML = """\
project_name: cyber-community-v2
current_phase: Phase 26B
current_goal: Implement T4 minimal activation.
next_expected_step: Run contract-flip tests and verify chain.
context_notes: Background context.
recent_progress:
  - item: Task A done
    completed: true
  - item: Task B pending
    completed: false
current_risks:
  - description: High risk alpha
    severity: high
    mitigation: Mitigate alpha
  - description: Medium risk beta
    severity: medium
"""

DECISION_LOG_YAML = """\
decisions:
  - date: "2026-03-20"
    title: Decision A
    decision: We chose approach A.
    rationale: Because it is simpler.
  - date: "2026-03-23"
    title: Decision B
    decision: We froze path B.
    rationale: Structural deadlock.
"""

ARTIFACT_DATA = {
    "project_name": "cyber-community-v2",
    "generated_at": "2026-03-24T09:00:00+00:00",
    "role": "claude",
    "task_summary": "Implement Phase 26B T4 activation.",
    "status": "partial",
    "files_changed": ["src/engine/t4_builder.py"],
    "implemented_items": ["Added social_event guard"],
    "tests_run": ["test_gate_opens — PASS", "test_adjust_t4 — FAIL"],
    "unresolved_items": ["test_adjust_t4 still failing"],
    "notes": "Gate opened correctly.",
}


def setup_project(tmp_path: Path) -> tuple[Path, Path]:
    """Write state files and one artifact. Returns (state_dir, artifact_path)."""
    state_dir = tmp_path / "projects" / "cyber-community-v2"
    state_dir.mkdir(parents=True)
    (state_dir / "project_charter.md").write_text(CHARTER, encoding="utf-8")
    (state_dir / "working_state.yaml").write_text(WORKING_STATE_YAML, encoding="utf-8")
    (state_dir / "decision_log.yaml").write_text(DECISION_LOG_YAML, encoding="utf-8")

    artifacts_dir = state_dir / "artifacts"
    artifacts_dir.mkdir()
    artifact_path = artifacts_dir / "run_2026-03-24T09-00-00.json"
    artifact_path.write_text(json.dumps(ARTIFACT_DATA), encoding="utf-8")

    return state_dir, artifact_path


# ---------------------------------------------------------------------------
# select_latest_artifact
# ---------------------------------------------------------------------------

class TestSelectLatestArtifact:
    def test_returns_latest_by_name(self, tmp_path):
        state_dir = tmp_path / "proj"
        artifacts_dir = state_dir / "artifacts"
        artifacts_dir.mkdir(parents=True)
        (artifacts_dir / "run_2026-03-23T10-00-00.json").write_text("{}")
        (artifacts_dir / "run_2026-03-24T09-00-00.json").write_text("{}")
        (artifacts_dir / "run_2026-03-22T08-00-00.json").write_text("{}")

        result = select_latest_artifact(state_dir)
        assert result.name == "run_2026-03-24T09-00-00.json"

    def test_single_artifact_returned(self, tmp_path):
        state_dir = tmp_path / "proj"
        artifacts_dir = state_dir / "artifacts"
        artifacts_dir.mkdir(parents=True)
        only = artifacts_dir / "run_2026-03-24T09-00-00.json"
        only.write_text("{}")

        assert select_latest_artifact(state_dir) == only

    def test_no_artifacts_dir_raises(self, tmp_path):
        state_dir = tmp_path / "proj"
        state_dir.mkdir()
        with pytest.raises(ReviewError, match="No artifacts directory"):
            select_latest_artifact(state_dir)

    def test_empty_artifacts_dir_raises(self, tmp_path):
        state_dir = tmp_path / "proj"
        (state_dir / "artifacts").mkdir(parents=True)
        with pytest.raises(ReviewError, match="No run artifacts"):
            select_latest_artifact(state_dir)


# ---------------------------------------------------------------------------
# _derive_inspect_next
# ---------------------------------------------------------------------------

class TestDeriveInspectNext:
    def _make_artifact(self, unresolved: list[str]) -> ImplementationRunArtifact:
        return ImplementationRunArtifact(
            project_name="p",
            generated_at="2026-03-24T00:00:00+00:00",
            role="claude",
            task_summary="t",
            status="partial",
            unresolved_items=unresolved,
        )

    def test_single_unresolved_returns_it_directly(self):
        artifact = self._make_artifact(["Fix the failing test"])
        result = _derive_inspect_next(artifact, "next step fallback")
        assert result == "Fix the failing test"

    def test_multiple_unresolved_lists_all(self):
        artifact = self._make_artifact(["Issue A", "Issue B"])
        result = _derive_inspect_next(artifact, "fallback")
        assert "Issue A" in result
        assert "Issue B" in result

    def test_no_unresolved_falls_back_to_next_step(self):
        artifact = self._make_artifact([])
        result = _derive_inspect_next(artifact, "  Run contract tests.  ")
        assert result == "Run contract tests."

    def test_no_unresolved_strips_whitespace_from_fallback(self):
        artifact = self._make_artifact([])
        result = _derive_inspect_next(artifact, "Next step.\n")
        assert not result.endswith("\n")


# ---------------------------------------------------------------------------
# generate_review_packet
# ---------------------------------------------------------------------------

class TestGenerateReviewPacket:
    def test_generates_valid_packet(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        assert isinstance(packet, ReviewPacket)

    def test_project_name_from_working_state(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        # packet.project_name comes from working_state.yaml
        assert packet.project_name == "cyber-community-v2"

    def test_includes_project_summary(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        assert packet.project_summary
        assert "Test project overview" in packet.project_summary

    def test_includes_run_summary(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        assert packet.run_summary.status == "partial"
        assert "Phase 26B" in packet.run_summary.task_summary
        assert "src/engine/t4_builder.py" in packet.run_summary.files_changed

    def test_includes_recent_progress(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        assert len(packet.recent_progress) == 2

    def test_includes_current_risks(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        assert len(packet.current_risks) == 2

    def test_includes_recent_decisions(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        assert len(packet.recent_decisions) == 2

    def test_inspect_next_from_unresolved(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        # Artifact has unresolved_items → inspect_next should reference them
        assert "test_adjust_t4" in packet.inspect_next

    def test_inspect_next_falls_back_to_next_step(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        # Override artifact with no unresolved items
        artifact_data = {**ARTIFACT_DATA, "unresolved_items": []}
        artifact_path = state_dir / "artifacts" / "run_2026-03-24T10-00-00.json"
        artifact_path.write_text(json.dumps(artifact_data))

        packet = generate_review_packet(state_dir)
        assert "contract-flip tests" in packet.inspect_next

    def test_auto_selects_latest_artifact(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        # Add a newer artifact with different task_summary
        newer_data = {**ARTIFACT_DATA, "generated_at": "2026-03-25T09:00:00+00:00",
                      "task_summary": "Newer task"}
        newer_path = state_dir / "artifacts" / "run_2026-03-25T09-00-00.json"
        newer_path.write_text(json.dumps(newer_data))

        packet = generate_review_packet(state_dir)
        assert packet.run_summary.task_summary == "Newer task"

    def test_explicit_artifact_path_used(self, tmp_path):
        state_dir, artifact_path = setup_project(tmp_path)
        packet = generate_review_packet(state_dir, artifact_path=artifact_path)
        assert packet.run_summary.task_summary == ARTIFACT_DATA["task_summary"]

    def test_no_artifacts_raises(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        for f in (state_dir / "artifacts").glob("*.json"):
            f.unlink()
        with pytest.raises(ReviewError, match="No run artifacts"):
            generate_review_packet(state_dir)

    def test_current_goal_stripped(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        assert not packet.current_goal.endswith("\n")


# ---------------------------------------------------------------------------
# save_review_packet
# ---------------------------------------------------------------------------

class TestSaveReviewPacket:
    def test_saved_to_expected_path(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        saved = save_review_packet(packet, state_dir)
        assert saved == state_dir / "review_packet.json"
        assert saved.exists()

    def test_saved_content_is_valid_json(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        packet = generate_review_packet(state_dir)
        saved = save_review_packet(packet, state_dir)
        data = json.loads(saved.read_text(encoding="utf-8"))
        assert "run_summary" in data
        assert data["project_name"] == "cyber-community-v2"

    def test_none_fields_excluded(self, tmp_path):
        state_dir, _ = setup_project(tmp_path)
        # Artifact with no notes
        artifact_data = {k: v for k, v in ARTIFACT_DATA.items() if k != "notes"}
        (state_dir / "artifacts" / "run_2026-03-24T09-00-00.json").write_text(
            json.dumps(artifact_data)
        )
        packet = generate_review_packet(state_dir)
        saved = save_review_packet(packet, state_dir)
        data = json.loads(saved.read_text())
        assert "notes" not in data.get("run_summary", {})
