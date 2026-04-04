"""Tests for orch.models — data structures."""
import json
import pytest
from pathlib import Path

from orch.models import (
    TaskContract,
    ReviewVerdict,
    Verdict,
    ExecutionEvidence,
    RoundResult,
    AttemptRecord,
)


class TestTaskContract:
    def test_from_dict_basic(self):
        data = {
            "phase_id": "P28",
            "task_key": "P28-T6",
            "title": "Calibrate ranges",
            "objective": "Calibrate signal intensity",
            "acceptance_criteria": ["tests pass"],
            "allowed_files": ["back/**/*.py"],
            "forbidden_files": ["docs/vision.md"],
        }
        tc = TaskContract.from_dict(data)
        assert tc.phase_id == "P28"
        assert tc.task_key == "P28-T6"
        assert tc.task_id == "P28-T6"  # backward compat property
        assert tc.description == "Calibrate signal intensity"
        assert tc.allowed_files == ["back/**/*.py"]

    def test_to_json_roundtrip(self):
        tc = TaskContract(
            phase_id="P1", task_key="P1-T1",
            title="Test", objective="Do something",
        )
        data = json.loads(tc.to_json())
        tc2 = TaskContract.from_dict(data)
        assert tc2.phase_id == tc.phase_id
        assert tc2.task_key == tc.task_key

    def test_from_dict_fallback_task_id(self):
        """task_id key should be accepted as fallback for task_key."""
        data = {"task_id": "P1-T1", "title": "x", "objective": "y"}
        tc = TaskContract.from_dict(data)
        assert tc.task_key == "P1-T1"

    def test_from_json_file(self, tmp_path):
        path = tmp_path / "task_contract.json"
        path.write_text(json.dumps({
            "phase_id": "P28", "task_key": "P28-T6",
            "title": "t", "objective": "o",
        }))
        tc = TaskContract.from_json_file(path)
        assert tc.task_key == "P28-T6"


class TestReviewVerdict:
    def test_pass_verdict(self):
        rv = ReviewVerdict(verdict=Verdict.PASS, confidence="high")
        assert rv.passed is True

    def test_fail_verdict(self):
        rv = ReviewVerdict(verdict=Verdict.FAIL)
        assert rv.passed is False

    def test_from_dict_pass(self):
        rv = ReviewVerdict.from_dict({"verdict": "PASS", "confidence": "high"})
        assert rv.verdict == Verdict.PASS

    def test_from_dict_fail_from_result_key(self):
        """Old 'result' key should work as fallback."""
        rv = ReviewVerdict.from_dict({"result": "FAIL", "rationale": "bad"})
        assert rv.verdict == Verdict.FAIL
        assert rv.rationale == "bad"

    def test_from_dict_revision_required(self):
        rv = ReviewVerdict.from_dict({"verdict": "REVISION_REQUIRED"})
        assert rv.verdict == Verdict.REVISION_REQUIRED
        assert rv.passed is False

    def test_hard_gate_fail(self):
        rv = ReviewVerdict.hard_gate_fail("pytest failed")
        assert rv.verdict == Verdict.FAIL
        assert rv.confidence == "high"
        assert "pytest failed" in rv.rationale

    def test_from_dict_blocker_fixes_fallback(self):
        """required_fixes should map to blocker_fixes."""
        rv = ReviewVerdict.from_dict({"result": "FAIL", "required_fixes": ["fix X"]})
        assert rv.blocker_fixes == ["fix X"]

    def test_to_json_roundtrip(self):
        rv = ReviewVerdict(
            verdict=Verdict.PASS, confidence="high",
            met_criteria=["criterion 1"],
        )
        data = json.loads(rv.to_json())
        rv2 = ReviewVerdict.from_dict(data)
        assert rv2.verdict == rv.verdict
        assert rv2.met_criteria == rv.met_criteria


class TestExecutionEvidence:
    def test_from_dict_fallback_fields(self):
        """status/changes_made should map to summary/files_changed."""
        data = {"status": "success", "changes_made": ["file.py"]}
        ev = ExecutionEvidence.from_dict(data)
        assert ev.summary == "success"
        assert ev.files_changed == ["file.py"]

    def test_standard_fields(self):
        data = {
            "summary": "done",
            "files_changed": ["a.py", "b.py"],
            "commands_run": ["pytest"],
            "test_results": "all pass",
        }
        ev = ExecutionEvidence.from_dict(data)
        assert ev.summary == "done"
        assert len(ev.files_changed) == 2


class TestRoundResult:
    def test_total_cost(self):
        task = TaskContract(phase_id="P1", task_key="P1-T1", title="t", objective="o")
        rv = ReviewVerdict(verdict=Verdict.PASS)
        ev = ExecutionEvidence()
        from orch.utils.evidence_collector import GitEvidence
        git_ev = GitEvidence()
        a1 = AttemptRecord(
            attempt_number=1, task=task, execution_evidence=ev,
            git_evidence=git_ev, review_verdict=rv, claude_cost_usd=1.5,
        )
        a2 = AttemptRecord(
            attempt_number=2, task=task, execution_evidence=ev,
            git_evidence=git_ev, review_verdict=rv, claude_cost_usd=0.8,
        )
        result = RoundResult(round_id="round-0001", task=task, attempts=[a1, a2])
        assert result.total_cost_usd == pytest.approx(2.3)

    def test_escalated_property(self):
        task = TaskContract(phase_id="P1", task_key="P1-T1", title="t", objective="o")
        result = RoundResult(round_id="r", task=task, final_passed=False, escalation_reason="failed")
        assert result.escalated is True
        result2 = RoundResult(round_id="r", task=task, final_passed=True)
        assert result2.escalated is False
