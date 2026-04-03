"""Executes a single Round: Designer → Executor → [Designer repair →] Executor → Reviewer."""
import json
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import click

from orch.agents.designer import DesignerAgent, TaskDefinition
from orch.agents.executor import ExecutorAgent, ExecutorEvidence, ExecutorResult
from orch.agents.reviewer import ReviewerAgent, ReviewResult
from orch.utils.evidence_collector import GitEvidence
from orch.utils.verification_runner import VerificationResults, VerificationStepResult


RUNTIME_DIRNAME = "runtime"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _elapsed(start: float) -> str:
    secs = time.time() - start
    if secs < 60:
        return f"{secs:.0f}s"
    return f"{secs / 60:.1f}m"


@dataclass
class AttemptRecord:
    attempt_number: int
    task_used: TaskDefinition
    executor_output: str
    executor_evidence: ExecutorEvidence
    executor_git_evidence: GitEvidence
    executor_success: bool
    executor_cost_usd: float
    reviewer_result: str
    reviewer_confidence: str
    reviewer_rationale: str
    reviewer_unmet_criteria: list[str]
    reviewer_required_fixes: list[str]
    reviewer_human_review_needed: bool
    reviewer_cost_usd: float
    verification_results: VerificationResults | None = None
    is_token_exhausted: bool = False

    @property
    def reviewer_passed(self) -> bool:
        return self.reviewer_result == "PASS"

    @property
    def reviewer_reason(self) -> str:
        return self.reviewer_rationale

    @property
    def reviewer_issues(self) -> list[str]:
        return self.reviewer_unmet_criteria

    @property
    def executor_output_truncated(self) -> str:
        return self.executor_output[:500]


@dataclass
class RoundResult:
    round_id: str
    task: TaskDefinition
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_passed: bool = False
    escalated: bool = False
    escalation_reason: str = ""
    designer_cost_usd: float = 0.0
    repair_cost_usd: float = 0.0

    @property
    def total_cost_usd(self) -> float:
        cost = self.designer_cost_usd + self.repair_cost_usd
        for a in self.attempts:
            cost += a.executor_cost_usd + a.reviewer_cost_usd
        return cost


def run_round(
    round_id: str,
    instruction: str,
    designer: DesignerAgent,
    executor: ExecutorAgent,
    reviewer: ReviewerAgent,
    round_dir: Path,
    codebase_path: Path | None = None,
    test_cmd: str | None = None,
    max_attempts: int = 2,
) -> RoundResult:
    """Run a complete round. Returns the result regardless of pass/fail."""

    round_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"  [{_ts()}] Designer planning task...", nl=False)
    t0 = time.time()
    task = designer.plan_next_task(instruction, round_id)
    click.echo(f" done ({_elapsed(t0)}, ${task.cost_usd:.4f})")
    click.echo(f"           Task: {task.title}")

    result = RoundResult(
        round_id=round_id,
        task=task,
        designer_cost_usd=task.cost_usd,
    )

    _write_task_files(round_dir, task, prefix="task")
    current_task = task

    for attempt_num in range(1, max_attempts + 1):
        attempt_label = f"Attempt {attempt_num}/{max_attempts}"
        click.echo(f"\n  [{_ts()}] --- {attempt_label} ---")

        if codebase_path:
            _inject_task_file(codebase_path, current_task)

        click.echo(f"  [{_ts()}] Executor running...", nl=False)
        t0 = time.time()
        prompt = _build_executor_prompt(current_task, use_file_ref=codebase_path is not None)
        exec_result = executor.run(prompt)
        click.echo(f" done ({_elapsed(t0)}, ${exec_result.cost_usd:.4f})")

        if exec_result.is_token_exhausted:
            click.echo("           !! Token limit hit — executor may be incomplete")
        if exec_result.evidence.summary:
            click.echo(f"           Summary: {exec_result.evidence.summary[:120]}")

        verification = None
        if codebase_path:
            click.echo(f"  [{_ts()}] Hard gate: pytest...", nl=False)
            t0 = time.time()
            pytest_passed, pytest_output = _run_pytest(codebase_path, test_cmd=test_cmd)
            verification = VerificationResults(
                steps=[VerificationStepResult(
                    command=test_cmd or "python -m pytest -v --tb=short",
                    exit_code=0 if pytest_passed else 1,
                    stdout=pytest_output[:1500],
                    stderr="",
                    passed=pytest_passed,
                )],
                all_passed=pytest_passed,
                summary="pytest PASSED" if pytest_passed else "pytest FAILED",
            )
            tag = click.style("PASS", fg="green") if pytest_passed else click.style("FAIL", fg="red")
            click.echo(f" {tag} ({_elapsed(t0)})")
            if not pytest_passed:
                click.echo(f"           pytest output (last 500 chars):\n{pytest_output[-500:]}")

        _write_execution_report(
            round_dir / f"execution_report_attempt_{attempt_num}.json",
            attempt_num, exec_result, verification,
        )

        if verification and not verification.all_passed:
            review_verdict = ReviewResult(
                result="FAIL",
                confidence="high",
                unmet_criteria=["pytest failed — hard gate"],
                suspicious_claims=[],
                required_fixes=["fix failing tests before proceeding"],
                human_review_needed=False,
                rationale=f"Hard gate: pytest failed. {verification.steps[0].stdout[-300:] if verification.steps else ''}",
            )
            click.echo(f"  [{_ts()}] Reviewer skipped — hard gate FAIL (pytest)")
        else:
            click.echo(f"  [{_ts()}] Soft gate: Reviewer evaluating...", nl=False)
            t0 = time.time()
            review_verdict = reviewer.review(task=current_task, exec_result=exec_result)
            verdict_color = "green" if review_verdict.passed else "red"
            verdict_text = click.style(review_verdict.result, fg=verdict_color, bold=True)
            click.echo(f" {verdict_text} ({_elapsed(t0)}, ${review_verdict.cost_usd:.4f})")
            click.echo(f"           Confidence: {review_verdict.confidence}")
            if not review_verdict.passed and review_verdict.unmet_criteria:
                for c in review_verdict.unmet_criteria[:3]:
                    click.echo(f"           Unmet: {c[:100]}")

        _write_review_files(round_dir, attempt_num, review_verdict)

        attempt = AttemptRecord(
            attempt_number=attempt_num,
            task_used=current_task,
            executor_output=exec_result.output,
            executor_evidence=exec_result.evidence,
            executor_git_evidence=exec_result.git_evidence,
            executor_success=exec_result.success,
            executor_cost_usd=exec_result.cost_usd,
            reviewer_result=review_verdict.result,
            reviewer_confidence=review_verdict.confidence,
            reviewer_rationale=review_verdict.rationale,
            reviewer_unmet_criteria=review_verdict.unmet_criteria,
            reviewer_required_fixes=review_verdict.required_fixes,
            reviewer_human_review_needed=review_verdict.human_review_needed,
            reviewer_cost_usd=review_verdict.cost_usd,
            verification_results=verification,
            is_token_exhausted=exec_result.is_token_exhausted,
        )
        result.attempts.append(attempt)
        _write_attempt_file(round_dir / f"attempt_{attempt_num}.md", attempt)

        if review_verdict.passed:
            result.final_passed = True
            break

        if attempt_num < max_attempts:
            click.echo(f"  [{_ts()}] Designer repairing task...", nl=False)
            t0 = time.time()
            repaired = designer.repair_task(current_task, review_verdict, exec_result.evidence)
            click.echo(f" done ({_elapsed(t0)}, ${repaired.cost_usd:.4f})")
            click.echo(f"           Repaired: {repaired.title}")
            result.repair_cost_usd += repaired.cost_usd
            current_task = repaired
            _write_task_files(round_dir, repaired, prefix=f"repaired_task_attempt_{attempt_num + 1}")
        else:
            click.echo(f"\n  [{_ts()}] Max attempts reached — escalating")
            result.escalated = True
            result.escalation_reason = _build_escalation_reason(result)

    _write_audit_file(round_dir / "audit.md", result)
    return result


def _build_executor_prompt(task: TaskDefinition, use_file_ref: bool = False) -> str:
    if use_file_ref:
        return (
            "Execute the task defined in .orch/runtime/current_task.md\n\n"
            "Read that file first for the full task definition, acceptance criteria, and required tests.\n\n"
            "Also check .orch/runtime/recent_rounds.md if it exists — it shows what was already done in recent rounds, so you don't redo completed work."
        )

    criteria = "\n".join(f"- {c}" for c in task.acceptance_criteria)
    required_tests = "\n".join(f"- {t}" for t in task.required_tests)
    non_goals = "\n".join(f"- {g}" for g in task.non_goals)
    constraints = "\n".join(f"- {c}" for c in task.constraints)

    parts = [
        f"# Task: {task.title}",
        f"\n## Objective\n{task.objective}",
        f"\n## Exact Scope\n{task.exact_scope}",
    ]
    if constraints:
        parts.append(f"\n## Constraints\n{constraints}")
    if criteria:
        parts.append(f"\n## Acceptance Criteria\n{criteria}")
    if required_tests:
        parts.append(f"\n## Required Tests\nYou must write tests covering:\n{required_tests}")
    if non_goals:
        parts.append(f"\n## Non-Goals (Do NOT do these)\n{non_goals}")
    return "\n".join(parts)


def _write_task_files(round_dir: Path, task: TaskDefinition, prefix: str) -> None:
    data = {
        "task_id": task.task_id,
        "title": task.title,
        "objective": task.objective,
        "exact_scope": task.exact_scope,
        "constraints": task.constraints,
        "acceptance_criteria": task.acceptance_criteria,
        "required_tests": task.required_tests,
        "non_goals": task.non_goals,
    }
    (round_dir / f"{prefix}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

    criteria = "\n".join(f"- {c}" for c in task.acceptance_criteria)
    required_tests = "\n".join(f"- {t}" for t in task.required_tests)
    non_goals = "\n".join(f"- {g}" for g in task.non_goals)
    md = (
        f"# Task: {task.title}\n\n"
        f"**ID:** {task.task_id}  \n"
        f"**Objective:** {task.objective}\n\n"
        f"**Exact Scope:** {task.exact_scope}\n\n"
    )
    if task.constraints:
        md += "## Constraints\n" + "\n".join(f"- {c}" for c in task.constraints) + "\n\n"
    if criteria:
        md += f"## Acceptance Criteria\n{criteria}\n\n"
    if required_tests:
        md += f"## Required Tests\n{required_tests}\n\n"
    if non_goals:
        md += f"## Non-Goals\n{non_goals}\n"
    (round_dir / f"{prefix}.md").write_text(md)


def _write_execution_report(path: Path, attempt_num: int, exec_result: ExecutorResult, verification: VerificationResults | None = None) -> None:
    ev = exec_result.evidence
    git_ev = exec_result.git_evidence
    data = {
        "attempt": attempt_num,
        "success": exec_result.success,
        "cost_usd": exec_result.cost_usd,
        "is_token_exhausted": exec_result.is_token_exhausted,
        "git_evidence": {
            "files_modified": git_ev.files_modified,
            "files_added": git_ev.files_added,
            "files_deleted": git_ev.files_deleted,
            "diff_stat": git_ev.diff_stat,
            "diff_patch_truncated": git_ev.diff_patch_truncated,
            "has_changes": git_ev.has_changes,
            "error": git_ev.error,
        },
        "hard_gate_pytest": None,
        "executor_reported": {
            "summary": ev.summary,
            "files_changed": ev.files_changed,
            "commands_run": ev.commands_run,
            "test_results": ev.test_results,
            "diff_summary": ev.diff_summary,
            "unresolved_issues": ev.unresolved_issues,
        },
        "full_output_truncated": exec_result.output[:2000],
    }
    if verification:
        data["hard_gate_pytest"] = {
            "summary": verification.summary,
            "all_passed": verification.all_passed,
            "output": verification.steps[0].stdout if verification.steps else "",
        }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _write_review_files(round_dir: Path, attempt_num: int, verdict: ReviewResult) -> None:
    data = {
        "attempt": attempt_num,
        "result": verdict.result,
        "confidence": verdict.confidence,
        "unmet_criteria": verdict.unmet_criteria,
        "suspicious_claims": verdict.suspicious_claims,
        "required_fixes": verdict.required_fixes,
        "human_review_needed": verdict.human_review_needed,
        "rationale": verdict.rationale,
        "cost_usd": verdict.cost_usd,
    }
    json_path = round_dir / f"review_attempt_{attempt_num}.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    md = (
        f"# Review — Attempt {attempt_num}: {verdict.result}\n\n"
        f"**Confidence:** {verdict.confidence}  \n"
        f"**Human review needed:** {verdict.human_review_needed}\n\n"
        f"## Rationale\n{verdict.rationale}\n\n"
    )
    if verdict.unmet_criteria:
        md += "## Unmet Criteria\n" + "\n".join(f"- {c}" for c in verdict.unmet_criteria) + "\n\n"
    if verdict.suspicious_claims:
        md += "## Suspicious Claims\n" + "\n".join(f"- {c}" for c in verdict.suspicious_claims) + "\n\n"
    if verdict.required_fixes:
        md += "## Required Fixes\n" + "\n".join(f"- {f}" for f in verdict.required_fixes) + "\n\n"
    (round_dir / f"review_attempt_{attempt_num}.md").write_text(md)


def _write_attempt_file(path: Path, attempt: AttemptRecord) -> None:
    ev = attempt.executor_evidence
    exhausted = "\n> ⚠ TOKEN EXHAUSTED" if attempt.is_token_exhausted else ""
    content = (
        f"# Attempt {attempt.attempt_number}{exhausted}\n\n"
        f"**Task:** {attempt.task_used.title}\n\n"
        f"## Execution Evidence (self-reported)\n"
        f"- Summary: {ev.summary}\n"
        f"- Commands run: {ev.commands_run or '(none)'}\n"
        f"- Test results: {ev.test_results or '(not run)'}\n"
        f"- Unresolved issues: {ev.unresolved_issues or '(none)'}\n\n"
        f"*(See execution_report_attempt_{attempt.attempt_number}.json for git-verified evidence)*\n\n"
        f"## Reviewer Verdict: {attempt.reviewer_result} (confidence: {attempt.reviewer_confidence})\n"
        f"{attempt.reviewer_rationale}\n\n"
        f"**Cost:** executor ${attempt.executor_cost_usd:.4f} | reviewer ${attempt.reviewer_cost_usd:.4f}\n"
    )
    if attempt.reviewer_unmet_criteria:
        content += "\n## Unmet Criteria\n" + "\n".join(f"- {c}" for c in attempt.reviewer_unmet_criteria) + "\n"
    if attempt.reviewer_required_fixes:
        content += "\n## Required Fixes\n" + "\n".join(f"- {f}" for f in attempt.reviewer_required_fixes) + "\n"
    path.write_text(content)


def _write_audit_file(path: Path, result: RoundResult) -> None:
    status = "ESCALATED" if result.escalated else "PASSED"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = (
        f"# Audit — Round {result.round_id}\n\n"
        f"**Status:** {status}  \n"
        f"**Completed:** {ts}  \n"
        f"**Total cost:** ${result.total_cost_usd:.4f}  \n"
        f"**Attempts:** {len(result.attempts)}\n\n"
        f"## Task\n{result.task.title} — {result.task.objective}\n\n"
    )
    if result.escalated:
        content += f"## Escalation Reason\n```\n{result.escalation_reason}\n```\n"
    path.write_text(content)


def _runtime_dir(codebase_path: Path) -> Path:
    return codebase_path / ".orch" / RUNTIME_DIRNAME


def _inject_task_file(codebase_path: Path, task: TaskDefinition) -> None:
    runtime_dir = _runtime_dir(codebase_path)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    criteria = "\n".join(f"- {c}" for c in task.acceptance_criteria)
    required_tests = "\n".join(f"- {t}" for t in task.required_tests)
    non_goals = "\n".join(f"- {g}" for g in task.non_goals)
    constraints = "\n".join(f"- {c}" for c in task.constraints)

    parts = [
        f"# Task: {task.title}",
        f"\n**ID:** {task.task_id}",
        f"\n## Objective\n{task.objective}",
        f"\n## Exact Scope\n{task.exact_scope}",
    ]
    if constraints:
        parts.append(f"\n## Constraints\n{constraints}")
    if criteria:
        parts.append(f"\n## Acceptance Criteria\n{criteria}")
    if required_tests:
        parts.append(f"\n## Required Tests\nYou must write tests covering:\n{required_tests}")
    if non_goals:
        parts.append(f"\n## Non-Goals (Do NOT do these)\n{non_goals}")

    (runtime_dir / "current_task.md").write_text("\n".join(parts) + "\n")


def inject_recent_rounds(codebase_path: Path, rounds_summary: str) -> None:
    runtime_dir = _runtime_dir(codebase_path)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "recent_rounds.md").write_text(rounds_summary)


def cleanup_round_docs(codebase_path: Path) -> None:
    runtime_dir = _runtime_dir(codebase_path)
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)


def _run_pytest(codebase_path: Path, test_cmd: str | None = None, timeout: int = 120) -> tuple[bool, str]:
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")

    try:
        if test_cmd:
            proc = subprocess.run(
                test_cmd,
                shell=True,
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
        else:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
        output = proc.stdout + proc.stderr
        return proc.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"pytest timed out after {timeout}s"
    except FileNotFoundError:
        return False, "python not found in PATH"


def _build_escalation_reason(result: RoundResult) -> str:
    lines = [f"Round {result.round_id} failed after {len(result.attempts)} attempt(s)."]
    for a in result.attempts:
        exhausted = " [TOKEN EXHAUSTED]" if a.is_token_exhausted else ""
        lines.append(f"\nAttempt {a.attempt_number}{exhausted}:")
        lines.append(f"  Task: {a.task_used.title}")
        lines.append(f"  Executor success: {a.executor_success}")
        lines.append(f"  Reviewer: {a.reviewer_result} (confidence: {a.reviewer_confidence})")
        lines.append(f"  Reason: {a.reviewer_rationale}")
        for fix in a.reviewer_required_fixes:
            lines.append(f"  Required fix: {fix}")
        for issue in a.reviewer_unmet_criteria:
            lines.append(f"  Unmet criterion: {issue}")
    return "\n".join(lines)
