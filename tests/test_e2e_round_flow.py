"""End-to-end round flow test with a real git repo and file-writing executor.

Uses MockProvider for LLM calls but a FileWritingMockExecutor that:
- Actually writes files to a temp git repo
- Triggers real git evidence collection
- Verifies that git-based evidence matches what was written

This tests the full contract from bootstrap → round → repair → PASS,
including git evidence, CLI artifact structure, and document updates.
"""
import json
import subprocess
from pathlib import Path

import pytest

from orch.agents.context import load_designer_context, load_reviewer_context
from orch.agents.designer import DesignerAgent
from orch.agents.executor import ExecutorEvidence, ExecutorResult
from orch.agents.reviewer import ReviewerAgent
from orch.engine.orchestrator import _needs_bootstrap, _run_bootstrap
from orch.engine.round_runner import run_round
from orch.providers.base import LLMProvider, LLMResponse
from orch.utils.evidence_collector import collect_git_evidence


# ── Helpers ───────────────────────────────────────────────────────────────────

class MockProvider(LLMProvider):
    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self._index = 0

    def complete(self, system: str, messages: list) -> LLMResponse:
        if self._index >= len(self._responses):
            raise RuntimeError(f"MockProvider exhausted after {self._index} calls")
        resp = self._responses[self._index]
        self._index += 1
        return resp

    @property
    def model_name(self) -> str:
        return "mock"


class FileWritingMockExecutor:
    """Mock executor that writes real files and collects real git evidence."""

    def __init__(self, codebase_path: Path, steps: list[dict]):
        """
        steps: list of dicts, one per call to run():
          {
            "files": {"path/to/file.py": "content"},
            "output": "execution summary text",
            "evidence_block": {...}  # optional <evidence> JSON
          }
        """
        self._codebase_path = codebase_path
        self._steps = steps
        self._index = 0

    def run(self, prompt: str) -> ExecutorResult:
        step = self._steps[self._index]
        self._index += 1

        # Write real files to the codebase
        for rel_path, content in step.get("files", {}).items():
            target = self._codebase_path / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

        # Build self-reported evidence
        ev_data = step.get("evidence_block", {})
        evidence = ExecutorEvidence(
            summary=ev_data.get("summary", step.get("output", "")[:100]),
            files_changed=ev_data.get("files_changed", list(step.get("files", {}).keys())),
            commands_run=ev_data.get("commands_run", []),
            test_results=ev_data.get("test_results", ""),
            diff_summary=ev_data.get("diff_summary", ""),
            unresolved_issues=ev_data.get("unresolved_issues", []),
        )

        # Collect REAL git evidence (this is the external collection we're testing)
        git_evidence = collect_git_evidence(self._codebase_path)

        return ExecutorResult(
            success=step.get("success", True),
            output=step.get("output", "Done."),
            cost_usd=0.0,
            session_id=f"mock-step-{self._index}",
            evidence=evidence,
            git_evidence=git_evidence,
        )


def _init_git_repo(path: Path) -> None:
    """Create a git repo with an initial commit for testing."""
    subprocess.run(["git", "init"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"],
                   cwd=str(path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"],
                   cwd=str(path), capture_output=True)
    # Initial empty commit so HEAD exists
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"],
                   cwd=str(path), capture_output=True)


def _make_project(tmp_path: Path) -> tuple[Path, Path]:
    """Create state_dir + codebase git repo, return (state_dir, codebase_path)."""
    state_dir = tmp_path / "orchestrator" / "projects" / "test-project"
    state_dir.mkdir(parents=True)
    (state_dir / "context").mkdir()
    (state_dir / "phases").mkdir()

    codebase = tmp_path / "codebase"
    codebase.mkdir()
    _init_git_repo(codebase)

    return state_dir, codebase


# ── Test: git evidence collection ─────────────────────────────────────────────

def test_git_evidence_detects_new_and_modified_files(tmp_path):
    """GitEvidence should reflect actual filesystem changes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    # Initially clean
    ev = collect_git_evidence(repo)
    assert not ev.has_changes
    assert ev.files_modified == []
    assert ev.files_added == []
    assert ev.error == ""

    # Create a new file (untracked)
    (repo / "new_file.py").write_text("x = 1\n")
    ev = collect_git_evidence(repo)
    assert ev.has_changes
    assert "new_file.py" in ev.files_added

    # Modify an existing tracked file
    subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
    subprocess.run(["git", "commit", "-m", "add new_file"], cwd=str(repo), capture_output=True)
    (repo / "new_file.py").write_text("x = 2\n")
    ev = collect_git_evidence(repo)
    assert ev.has_changes
    assert "new_file.py" in ev.files_modified
    assert ev.diff_stat != ""
    # diff_patch should contain the actual change
    assert "new_file.py" in ev.diff_patch_truncated


def test_git_evidence_empty_for_non_repo(tmp_path):
    """Non-git directory (or non-existent path) returns error, not crash."""
    # Non-existent path
    ev = collect_git_evidence(tmp_path / "not_a_repo")
    assert ev.error != ""
    assert not ev.has_changes

    # Existing dir that is not a git repo
    plain_dir = tmp_path / "plain"
    plain_dir.mkdir()
    ev2 = collect_git_evidence(plain_dir)
    assert ev2.error != ""
    assert not ev2.has_changes


# ── Test: bootstrap mode ─────────────────────────────────────────────────────

def test_bootstrap_generates_real_files(tmp_path):
    """Bootstrap mode writes current_phase.md and context/designer.md."""
    state_dir, _ = _make_project(tmp_path)

    vision_content = """\
# Calculator CLI

## 项目目标
A Python CLI calculator that supports add, subtract, multiply, divide.

## 核心功能
- add(a, b)
- subtract(a, b)
- multiply(a, b)
- divide(a, b) with zero-division protection

## 技术栈
Python 3.11, no external deps

## 不做什么
No GUI, no history, no persistence
"""
    (state_dir / "vision.md").write_text(vision_content)
    (state_dir / "current_phase.md").write_text("bootstrap_needed: true")
    (state_dir / "context" / "designer.md").write_text("# Designer Context\n")

    bootstrap_response = json.dumps({
        "current_phase_md": (
            "# Phase 1: Core Calculator\n\n"
            "## Phase Goal\nImplement all four arithmetic operations.\n\n"
            "## In Scope\n- add, subtract, multiply, divide\n\n"
            "## Task Queue\n"
            "- [ ] T001: implement add\n"
            "- [ ] T002: implement subtract\n"
            "- [ ] T003: implement multiply\n"
            "- [ ] T004: implement divide with zero protection\n\n"
            "## Completed Tasks\n(none yet)\n\n"
            "## Current Status\nbootstrapped — ready to start T001\n\n"
            "## Risks / Blockers\n- none\n\n"
            "## Next Recommended Task\nT001"
        ),
        "designer_context_md": (
            "# Designer Context\n\n"
            "## Active Constraints\n- Python 3.11, no external deps\n\n"
            "## Working Assumptions\n- pure functions, no state\n\n"
            "## Architecture Snapshot\ncalculator.py with four functions\n\n"
            "## Known Risks\n- divide by zero\n\n"
            "## Open Questions For Human\n- (none)"
        ),
    })

    from orch.config.settings import OrchestratorConfig
    provider = MockProvider([
        LLMResponse(content=bootstrap_response, input_tokens=200, output_tokens=300, cost_usd=0.002),
    ])
    designer = DesignerAgent(provider, state_dir)

    assert _needs_bootstrap(state_dir)

    config = OrchestratorConfig()
    _run_bootstrap(designer, state_dir, config)

    phase = (state_dir / "current_phase.md").read_text()
    ctx = (state_dir / "context" / "designer.md").read_text()

    assert "T001" in phase
    assert "bootstrap_needed" not in phase
    assert "Phase 1" in phase
    assert "Active Constraints" in ctx
    assert "Architecture Snapshot" in ctx

    assert not _needs_bootstrap(state_dir)


# ── Test: full round flow with real git evidence ───────────────────────────────

def test_full_round_pass_with_real_git_evidence(tmp_path):
    """Complete PASS round: real files written, git evidence collected, reviewer PASS."""
    state_dir, codebase = _make_project(tmp_path)

    (state_dir / "vision.md").write_text("# Calculator\nBuild a Python calculator.")
    (state_dir / "current_phase.md").write_text(
        "# Phase 1\n## Task Queue\n- [ ] T001: implement add\n## Next Recommended Task\nT001"
    )
    (state_dir / "context" / "designer.md").write_text("# Designer Context\n## Active Constraints\n- Python 3.11")

    task_json = json.dumps({
        "task_id": "round-0001",
        "title": "Implement add function",
        "objective": "Create add(a, b) in calculator.py",
        "exact_scope": "Only the add function",
        "likely_files": ["calculator.py"],
        "constraints": [],
        "acceptance_criteria": ["calculator.py exists", "add(2, 3) returns 5"],
        "verification_steps": ["python -c 'from calculator import add; assert add(2,3)==5'"],
        "non_goals": [],
    })

    review_pass = json.dumps({
        "result": "PASS",
        "confidence": "high",
        "unmet_criteria": [],
        "suspicious_claims": [],
        "required_fixes": [],
        "human_review_needed": False,
        "rationale": "calculator.py is present in git-verified files_added, objective met",
    })

    designer = DesignerAgent(
        MockProvider([LLMResponse(content=task_json, input_tokens=100, output_tokens=100, cost_usd=0.001)]),
        state_dir,
    )
    reviewer = ReviewerAgent(
        MockProvider([LLMResponse(content=review_pass, input_tokens=100, output_tokens=100, cost_usd=0.001)]),
        state_dir,
    )
    executor = FileWritingMockExecutor(codebase, [
        {
            "files": {"calculator.py": "def add(a, b):\n    return a + b\n"},
            "output": "Created calculator.py with add function.",
            "evidence_block": {
                "summary": "created add function",
                "commands_run": ["python -c 'from calculator import add; assert add(2,3)==5'"],
                "test_results": "assertion passed",
            },
        }
    ])

    round_dir = tmp_path / "round-0001"
    result = run_round(
        round_id="round-0001",
        instruction="implement add function",
        designer=designer,
        executor=executor,
        reviewer=reviewer,
        round_dir=round_dir,
    )

    assert result.final_passed
    assert len(result.attempts) == 1

    # Verify git evidence was collected and reflects actual file creation
    attempt = result.attempts[0]
    git_ev = attempt.executor_git_evidence
    assert git_ev.has_changes, "git should detect calculator.py was created"
    assert "calculator.py" in git_ev.files_added, f"expected in files_added, got: {git_ev.files_added}"
    assert git_ev.error == ""

    # Verify execution report contains git evidence
    exec_report = json.loads((round_dir / "execution_report_attempt_1.json").read_text())
    assert exec_report["git_evidence"]["has_changes"]
    assert "calculator.py" in exec_report["git_evidence"]["files_added"]

    # Verify task.json structure
    task_data = json.loads((round_dir / "task.json").read_text())
    assert task_data["task_id"] == "round-0001"
    assert isinstance(task_data["acceptance_criteria"], list)

    # Verify review_attempt_1.json
    review_data = json.loads((round_dir / "review_attempt_1.json").read_text())
    assert review_data["result"] == "PASS"
    assert review_data["confidence"] == "high"

    # Verify file physically exists in codebase
    assert (codebase / "calculator.py").exists()


def test_full_round_fail_repair_pass_with_git(tmp_path):
    """FAIL on attempt 1 (no commands run) → repair → PASS on attempt 2 with evidence."""
    state_dir, codebase = _make_project(tmp_path)

    (state_dir / "vision.md").write_text("# Calculator\nBuild add + tests.")
    (state_dir / "current_phase.md").write_text(
        "# Phase 1\n## Task Queue\n- [ ] T001: implement add with tests\n## Next Recommended Task\nT001"
    )
    (state_dir / "context" / "designer.md").write_text("# Designer Context\n")

    task_json = json.dumps({
        "task_id": "round-0001",
        "title": "Implement add with tests",
        "objective": "Create add(a, b) AND write pytest tests",
        "exact_scope": "calculator.py + test_calculator.py",
        "likely_files": ["calculator.py", "test_calculator.py"],
        "constraints": [],
        "acceptance_criteria": ["calculator.py exists", "test_calculator.py exists", "tests pass"],
        "verification_steps": ["pytest test_calculator.py -v"],
        "non_goals": [],
    })

    review_fail = json.dumps({
        "result": "FAIL",
        "confidence": "high",
        "unmet_criteria": ["test_calculator.py exists — not found in git evidence"],
        "suspicious_claims": ["claimed tests pass but test file absent"],
        "required_fixes": ["create test_calculator.py with at least one test"],
        "human_review_needed": False,
        "rationale": "git-verified files_added only shows calculator.py, test file missing",
    })

    repaired_task_json = json.dumps({
        "task_id": "round-0001-repair",
        "title": "Implement add with tests (repaired)",
        "objective": "Create calculator.py AND test_calculator.py with passing tests",
        "exact_scope": "BOTH files must appear in git-verified changes",
        "likely_files": ["calculator.py", "test_calculator.py"],
        "constraints": ["must create test file — this was the failure point"],
        "acceptance_criteria": [
            "calculator.py exists in git",
            "test_calculator.py exists in git",
            "pytest test_calculator.py exits 0",
        ],
        "verification_steps": ["pytest test_calculator.py -v"],
        "non_goals": [],
    })

    review_pass = json.dumps({
        "result": "PASS",
        "confidence": "high",
        "unmet_criteria": [],
        "suspicious_claims": [],
        "required_fixes": [],
        "human_review_needed": False,
        "rationale": "both files in git files_added, verification step ran",
    })

    designer = DesignerAgent(
        MockProvider([
            LLMResponse(content=task_json, input_tokens=100, output_tokens=100, cost_usd=0.001),
            LLMResponse(content=repaired_task_json, input_tokens=150, output_tokens=150, cost_usd=0.0015),
        ]),
        state_dir,
    )
    reviewer = ReviewerAgent(
        MockProvider([
            LLMResponse(content=review_fail, input_tokens=100, output_tokens=100, cost_usd=0.001),
            LLMResponse(content=review_pass, input_tokens=100, output_tokens=100, cost_usd=0.001),
        ]),
        state_dir,
    )
    executor = FileWritingMockExecutor(codebase, [
        {
            # Attempt 1: only creates calculator.py, forgets test file
            "files": {"calculator.py": "def add(a, b):\n    return a + b\n"},
            "output": "Created calculator.py.",
        },
        {
            # Attempt 2: creates both files
            "files": {
                "calculator.py": "def add(a, b):\n    return a + b\n",
                "test_calculator.py": "from calculator import add\ndef test_add():\n    assert add(2, 3) == 5\n",
            },
            "output": "Created both files.",
            "evidence_block": {
                "summary": "created calculator.py and test_calculator.py",
                "commands_run": ["pytest test_calculator.py -v"],
                "test_results": "1 passed",
            },
        },
    ])

    round_dir = tmp_path / "round-0001"
    result = run_round(
        round_id="round-0001",
        instruction="implement add with tests",
        designer=designer,
        executor=executor,
        reviewer=reviewer,
        round_dir=round_dir,
    )

    assert result.final_passed
    assert len(result.attempts) == 2
    assert result.repair_cost_usd > 0

    # Attempt 1: git shows only calculator.py
    ev1 = result.attempts[0].executor_git_evidence
    assert "calculator.py" in ev1.files_added
    assert "test_calculator.py" not in ev1.files_added

    # Attempt 2: git shows both files (test file is new, calculator is now modified)
    ev2 = result.attempts[1].executor_git_evidence
    all_changed_2 = ev2.files_modified + ev2.files_added
    assert "test_calculator.py" in all_changed_2

    # Repaired task file exists
    assert (round_dir / "repaired_task_attempt_2.json").exists()
    repaired = json.loads((round_dir / "repaired_task_attempt_2.json").read_text())
    assert "repaired" in repaired["title"]

    # review_attempt_1 is FAIL, review_attempt_2 is PASS
    r1 = json.loads((round_dir / "review_attempt_1.json").read_text())
    r2 = json.loads((round_dir / "review_attempt_2.json").read_text())
    assert r1["result"] == "FAIL"
    assert r2["result"] == "PASS"

    # Execution reports contain git evidence
    exec1 = json.loads((round_dir / "execution_report_attempt_1.json").read_text())
    assert exec1["git_evidence"]["has_changes"]
    assert "calculator.py" in exec1["git_evidence"]["files_added"]
    assert "test_calculator.py" not in exec1["git_evidence"]["files_added"]

    exec2 = json.loads((round_dir / "execution_report_attempt_2.json").read_text())
    all_git_files_2 = exec2["git_evidence"]["files_modified"] + exec2["git_evidence"]["files_added"]
    assert "test_calculator.py" in all_git_files_2


# ── Test: CLI log reads new artifacts ─────────────────────────────────────────

def test_cli_log_reads_new_json_artifacts(tmp_path):
    """orch log <round_id> should display task.json + review_attempt_N.json data."""
    from click.testing import CliRunner
    from orch.cli.log_cmds import log_cmd
    from orch.db.database import create_project, set_active_project, init_db

    runner = CliRunner()

    # Set up a minimal round directory structure
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "phases" / "phase-0001" / "round-0001").mkdir(parents=True)
    round_dir = state_dir / "phases" / "phase-0001" / "round-0001"

    # Write all new-format artifacts
    (round_dir / "task.json").write_text(json.dumps({
        "task_id": "round-0001",
        "title": "Test Task",
        "objective": "Do the thing",
        "exact_scope": "only this",
        "likely_files": ["foo.py"],
        "constraints": [],
        "acceptance_criteria": ["foo.py created"],
        "verification_steps": [],
        "non_goals": [],
    }))

    (round_dir / "execution_report_attempt_1.json").write_text(json.dumps({
        "attempt": 1,
        "success": True,
        "cost_usd": 0.005,
        "is_token_exhausted": False,
        "git_evidence": {
            "files_modified": [],
            "files_added": ["foo.py"],
            "files_deleted": [],
            "diff_stat": "foo.py | 1 +\n1 file changed",
            "diff_patch_truncated": "diff --git a/foo.py b/foo.py\n+x = 1",
            "has_changes": True,
            "error": "",
        },
        "executor_reported": {
            "summary": "created foo.py",
            "files_changed": ["foo.py"],
            "commands_run": [],
            "test_results": "",
            "diff_summary": "added x = 1",
            "unresolved_issues": [],
        },
        "full_output_truncated": "Done.",
    }))

    (round_dir / "review_attempt_1.json").write_text(json.dumps({
        "attempt": 1,
        "result": "PASS",
        "confidence": "high",
        "unmet_criteria": [],
        "suspicious_claims": [],
        "required_fixes": [],
        "human_review_needed": False,
        "rationale": "foo.py is in git files_added",
        "cost_usd": 0.001,
    }))

    (round_dir / "audit.md").write_text(
        "# Audit — Round round-0001\n\n**Status:** PASSED  \n**Total cost:** $0.0060\n"
    )

    # Use isolated DB to avoid polluting global ~/.orch/orchestrator.db
    import orch.db.database as _db
    from orch.db.database import get_connection as _gc
    _orig_db_path = _db.DB_PATH
    _db.DB_PATH = tmp_path / ".orch" / "orchestrator.db"
    (tmp_path / ".orch").mkdir(exist_ok=True)
    try:
        init_db()
        project_id = f"test-{tmp_path.name[:20]}"
        project_name = f"Test {tmp_path.name[:20]}"
        create_project(project_id, project_name, str(tmp_path / "codebase"), str(state_dir))
        set_active_project(project_id)

        result = runner.invoke(log_cmd, ["round-0001"])

        assert result.exit_code == 0, f"log failed:\n{result.output}"
        output = result.output
        assert "Test Task" in output        # task title
        assert "Do the thing" in output     # objective
        assert "foo.py" in output           # file from git evidence
        assert "PASS" in output             # review result
        assert "foo.py is in git files_added" in output  # rationale
    finally:
        # Restore global DB path (isolated DB file is cleaned up with tmp_path)
        _db.DB_PATH = _orig_db_path
