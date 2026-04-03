"""Integration tests for round contract: task package → execution evidence → review verdict."""
import json
from pathlib import Path

import pytest

from orch.agents.context import load_designer_context
from orch.agents.designer import DesignerAgent
from orch.agents.executor import ExecutorEvidence, ExecutorResult
from orch.agents.reviewer import ReviewResult
from orch.engine.round_runner import run_round
from orch.providers.base import LLMProvider, LLMResponse


# ── Mock helpers ──────────────────────────────────────────────────────────────

class MockProvider(LLMProvider):
    """LLM provider that returns predefined responses in sequence."""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self._index = 0

    def complete(self, system: str, messages: list) -> LLMResponse:
        if self._index >= len(self._responses):
            raise RuntimeError(f"MockProvider exhausted ({self._index} calls made, {len(self._responses)} configured)")
        resp = self._responses[self._index]
        self._index += 1
        return resp

    @property
    def model_name(self) -> str:
        return "mock"


class MockExecutor:
    """Executor that returns predefined ExecutorResults in sequence."""

    def __init__(self, results: list[ExecutorResult]):
        self._results = list(results)
        self._index = 0

    def run(self, prompt: str) -> ExecutorResult:
        if self._index >= len(self._results):
            raise RuntimeError("MockExecutor exhausted")
        result = self._results[self._index]
        self._index += 1
        return result


class MockReviewer:
    """Reviewer that returns predefined ReviewResults in sequence."""

    def __init__(self, results: list[ReviewResult]):
        self._results = list(results)
        self._index = 0

    def review(self, task, exec_result) -> ReviewResult:
        if self._index >= len(self._results):
            raise RuntimeError("MockReviewer exhausted")
        result = self._results[self._index]
        self._index += 1
        return result


def _make_state_dir(tmp_path: Path) -> Path:
    state_dir = tmp_path / "project"
    state_dir.mkdir()
    (state_dir / "vision.md").write_text("# Vision\nBuild a Python calculator CLI.")
    (state_dir / "current_phase.md").write_text(
        "# Phase 1\n## Task Queue\n- [ ] T001: implement add function\n## Next Recommended Task\nT001"
    )
    (state_dir / "context").mkdir()
    (state_dir / "context" / "designer.md").write_text("# Designer Context\n## Active Constraints\n- Python 3.11")
    return state_dir


def _task_json(round_id: str = "round-0001", objective: str = "Create add(a, b) in calculator.py") -> str:
    return json.dumps({
        "task_id": round_id,
        "title": "Implement add function",
        "objective": objective,
        "exact_scope": "Only the add function in calculator.py",
        "constraints": [],
        "acceptance_criteria": ["calculator.py exists", "add(2, 3) returns 5"],
        "required_tests": ["test that add returns correct sum"],
        "non_goals": ["multiply, subtract"],
    })


def _review_pass(rationale: str = "all criteria met") -> ReviewResult:
    return ReviewResult(
        result="PASS",
        confidence="high",
        unmet_criteria=[],
        suspicious_claims=[],
        required_fixes=[],
        human_review_needed=False,
        rationale=rationale,
        cost_usd=0.001,
    )


def _review_fail(reason: str = "tests not run") -> ReviewResult:
    return ReviewResult(
        result="FAIL",
        confidence="high",
        unmet_criteria=["add(2,3)==5 — no test evidence provided"],
        suspicious_claims=["claimed success but no commands_run"],
        required_fixes=["run the verification step and show output"],
        human_review_needed=False,
        rationale=reason,
        cost_usd=0.001,
    )


def _make_evidence(files=None, commands=None, test_results="", unresolved=None) -> ExecutorEvidence:
    return ExecutorEvidence(
        summary="Created calculator.py",
        files_changed=files or ["calculator.py"],
        commands_run=commands or [],
        test_results=test_results,
        diff_summary="added add(a, b) returning a+b",
        unresolved_issues=unresolved or [],
    )


# ── Test: decisions.md NEVER in AI context ────────────────────────────────────

def test_decisions_md_excluded_from_designer_context(tmp_path):
    """decisions.md must never appear in designer context."""
    state_dir = _make_state_dir(tmp_path)
    (state_dir / "decisions.md").write_text(
        "# Decisions\n## 2024-01-01 — Secret\n**决定:** confidential decision"
    )

    designer_ctx = load_designer_context(state_dir)

    assert "decisions.md" not in designer_ctx, "decisions.md key must not appear in designer context"

    all_designer_text = " ".join(designer_ctx.values())
    assert "confidential decision" not in all_designer_text
    assert "Secret" not in all_designer_text


def test_designer_context_includes_designer_md(tmp_path):
    """Designer context must include context/designer.md."""
    state_dir = _make_state_dir(tmp_path)

    designer_ctx = load_designer_context(state_dir)
    assert "context/designer.md" in designer_ctx


# ── Test: PASS on first attempt ───────────────────────────────────────────────

def test_pass_on_first_attempt(tmp_path):
    state_dir = _make_state_dir(tmp_path)

    designer_provider = MockProvider([
        LLMResponse(content=_task_json(), input_tokens=100, output_tokens=100, cost_usd=0.001),
    ])
    mock_exec = MockExecutor([
        ExecutorResult(
            success=True, output="Done.", cost_usd=0.005, session_id="s1",
            evidence=_make_evidence(
                commands=["python -c 'from calculator import add; assert add(2,3)==5'"],
                test_results="assertion passed",
            ),
        ),
    ])
    mock_reviewer = MockReviewer([_review_pass()])

    designer = DesignerAgent(designer_provider, state_dir)
    round_dir = tmp_path / "round-0001"

    result = run_round(
        round_id="round-0001",
        instruction="implement add function",
        designer=designer,
        executor=mock_exec,
        reviewer=mock_reviewer,
        round_dir=round_dir,
    )

    assert result.final_passed
    assert not result.escalated
    assert len(result.attempts) == 1
    assert result.attempts[0].reviewer_result == "PASS"
    assert result.attempts[0].reviewer_confidence == "high"
    assert result.repair_cost_usd == 0.0

    # Verify structured files written
    assert (round_dir / "task.json").exists()
    assert (round_dir / "task.md").exists()
    assert (round_dir / "review_attempt_1.json").exists()
    assert (round_dir / "review_attempt_1.md").exists()
    assert (round_dir / "execution_report_attempt_1.json").exists()
    assert (round_dir / "audit.md").exists()

    # No repair files
    assert not (round_dir / "repaired_task_attempt_2.json").exists()

    # Verify task.json structure
    task_data = json.loads((round_dir / "task.json").read_text())
    assert task_data["task_id"] == "round-0001"
    assert "acceptance_criteria" in task_data
    assert isinstance(task_data["acceptance_criteria"], list)
    assert "required_tests" in task_data

    # Verify review_attempt_1.json structure
    review_data = json.loads((round_dir / "review_attempt_1.json").read_text())
    assert review_data["result"] == "PASS"
    assert "unmet_criteria" in review_data
    assert "required_fixes" in review_data


# ── Test: FAIL then repair then PASS ─────────────────────────────────────────

def test_fail_triggers_repair_step_then_pass(tmp_path):
    state_dir = _make_state_dir(tmp_path)

    repaired_task_json = json.dumps({
        "task_id": "round-0001-repair",
        "title": "Implement add function with verification",
        "objective": "Create add(a,b) AND run the verification command",
        "exact_scope": "calculator.py + must run verification",
        "constraints": ["must run verification step before claiming done"],
        "acceptance_criteria": ["calculator.py exists", "verification command output shows assertion passed"],
        "required_tests": ["test that add returns correct sum"],
        "non_goals": [],
    })

    designer_provider = MockProvider([
        LLMResponse(content=_task_json(), input_tokens=100, output_tokens=100, cost_usd=0.001),
        LLMResponse(content=repaired_task_json, input_tokens=150, output_tokens=150, cost_usd=0.0015),
    ])
    mock_exec = MockExecutor([
        # Attempt 1: no commands run → FAIL
        ExecutorResult(
            success=True, output="Created file.", cost_usd=0.005, session_id="s1",
            evidence=_make_evidence(commands=[], test_results=""),
        ),
        # Attempt 2: commands run → PASS
        ExecutorResult(
            success=True, output="File exists, assertion passed.", cost_usd=0.005, session_id="s2",
            evidence=_make_evidence(
                commands=["python -c 'from calculator import add; assert add(2,3)==5'"],
                test_results="assertion passed",
            ),
        ),
    ])
    mock_reviewer = MockReviewer([
        _review_fail(),
        _review_pass("evidence confirms assertion passed"),
    ])

    designer = DesignerAgent(designer_provider, state_dir)
    round_dir = tmp_path / "round-0001"

    result = run_round(
        round_id="round-0001",
        instruction="implement add function",
        designer=designer,
        executor=mock_exec,
        reviewer=mock_reviewer,
        round_dir=round_dir,
    )

    assert result.final_passed
    assert len(result.attempts) == 2

    # Repair step must have happened
    assert result.repair_cost_usd > 0

    # Attempt 2 used a different (repaired) task
    assert result.attempts[0].task_used.objective == "Create add(a, b) in calculator.py"
    assert result.attempts[1].task_used.objective == "Create add(a,b) AND run the verification command"

    # Review files for both attempts
    assert (round_dir / "review_attempt_1.json").exists()
    assert (round_dir / "review_attempt_2.json").exists()

    review_1 = json.loads((round_dir / "review_attempt_1.json").read_text())
    review_2 = json.loads((round_dir / "review_attempt_2.json").read_text())
    assert review_1["result"] == "FAIL"
    assert review_2["result"] == "PASS"

    # Repaired task file written
    assert (round_dir / "repaired_task_attempt_2.json").exists()

    # Execution reports for both attempts
    assert (round_dir / "execution_report_attempt_1.json").exists()
    assert (round_dir / "execution_report_attempt_2.json").exists()

    exec_report_1 = json.loads((round_dir / "execution_report_attempt_1.json").read_text())
    assert exec_report_1["executor_reported"]["commands_run"] == []
    exec_report_2 = json.loads((round_dir / "execution_report_attempt_2.json").read_text())
    assert len(exec_report_2["executor_reported"]["commands_run"]) > 0


# ── Test: FAIL twice → escalate ───────────────────────────────────────────────

def test_double_fail_escalates(tmp_path):
    state_dir = _make_state_dir(tmp_path)

    designer_provider = MockProvider([
        LLMResponse(content=_task_json(), input_tokens=100, output_tokens=100, cost_usd=0.001),
        LLMResponse(content=_task_json("round-0001-repair"), input_tokens=100, output_tokens=100, cost_usd=0.001),
    ])
    mock_exec = MockExecutor([
        ExecutorResult(success=False, output="Error", cost_usd=0.0, session_id="",
                       evidence=_make_evidence()),
        ExecutorResult(success=False, output="Error again", cost_usd=0.0, session_id="",
                       evidence=_make_evidence()),
    ])
    mock_reviewer = MockReviewer([
        _review_fail("first fail"),
        _review_fail("second fail"),
    ])

    designer = DesignerAgent(designer_provider, state_dir)
    round_dir = tmp_path / "round-0001"

    result = run_round(
        round_id="round-0001",
        instruction="implement add function",
        designer=designer,
        executor=mock_exec,
        reviewer=mock_reviewer,
        round_dir=round_dir,
    )

    assert not result.final_passed
    assert result.escalated
    assert len(result.attempts) == 2
    assert "second fail" in result.escalation_reason

    # Audit file must exist and note escalation
    audit = (round_dir / "audit.md").read_text()
    assert "ESCALATED" in audit


# ── Test: bootstrap detection ─────────────────────────────────────────────────

def test_bootstrap_detection(tmp_path):
    from orch.engine.orchestrator import _needs_bootstrap

    state_dir = tmp_path / "project"
    state_dir.mkdir()

    # Missing file → bootstrap needed
    assert _needs_bootstrap(state_dir)

    # Template content with bootstrap_needed marker
    (state_dir / "current_phase.md").write_text("# Phase — bootstrap_needed\n## Current Status\nbootstrap_needed")
    assert _needs_bootstrap(state_dir)

    # Old Chinese template marker
    (state_dir / "current_phase.md").write_text("**阶段名称：** 待规划")
    assert _needs_bootstrap(state_dir)

    # Real phase content → no bootstrap needed
    (state_dir / "current_phase.md").write_text(
        "# Phase 1: Calculator\n## Task Queue\n- [ ] T001: implement add"
    )
    assert not _needs_bootstrap(state_dir)


# ── Test: task package fields ─────────────────────────────────────────────────

def test_task_definition_backward_compat(tmp_path):
    """TaskDefinition.description must still work (used in orchestrator.py)."""
    from orch.agents.designer import TaskDefinition

    task = TaskDefinition(
        task_id="round-0001",
        title="Test task",
        objective="Do the thing",
        exact_scope="only this thing",
        acceptance_criteria=["thing is done"],
        verification_steps=[],
        non_goals=[],
        required_tests=["test that thing works"],
    )

    # backward compat
    assert task.description == "Do the thing"
    assert task.context_notes == ""

    # to_json works
    data = json.loads(task.to_json())
    assert data["task_id"] == "round-0001"
    assert isinstance(data["acceptance_criteria"], list)
    assert "required_tests" in data


# ── Test: review result backward compat ───────────────────────────────────────

def test_review_result_backward_compat():
    from orch.agents.reviewer import ReviewResult

    verdict = ReviewResult(
        result="FAIL",
        confidence="medium",
        unmet_criteria=["criterion A"],
        suspicious_claims=[],
        required_fixes=["fix this"],
        human_review_needed=False,
        rationale="things failed",
    )

    assert not verdict.passed
    assert verdict.reason == "things failed"
    assert verdict.issues == ["criterion A"]
