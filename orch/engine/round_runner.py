"""Executes a single Round: Designer → Executor → Reviewer (with one retry)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from orch.agents.designer import DesignerAgent, TaskDefinition
from orch.agents.executor import ExecutorAgent, ExecutorResult
from orch.agents.reviewer import ReviewerAgent, ReviewVerdict


@dataclass
class AttemptRecord:
    attempt_number: int
    executor_output: str
    executor_success: bool
    executor_cost_usd: float
    reviewer_passed: bool
    reviewer_reason: str
    reviewer_issues: list[str]
    reviewer_cost_usd: float
    is_token_exhausted: bool = False


@dataclass
class RoundResult:
    round_id: str
    task: TaskDefinition
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_passed: bool = False
    escalated: bool = False
    escalation_reason: str = ""
    designer_cost_usd: float = 0.0

    @property
    def total_cost_usd(self) -> float:
        cost = self.designer_cost_usd
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
    max_attempts: int = 2,
) -> RoundResult:
    """Run a complete round. Returns the result regardless of pass/fail."""

    # Step 1: Designer plans the task
    task = designer.plan_next_task(instruction)
    result = RoundResult(
        round_id=round_id,
        task=task,
        designer_cost_usd=task.cost_usd,
    )

    # Save task definition
    round_dir.mkdir(parents=True, exist_ok=True)
    _write_task_file(round_dir / "task.md", task)

    # Step 2: Executor + Reviewer loop (up to max_attempts)
    for attempt_num in range(1, max_attempts + 1):
        prompt = _build_executor_prompt(task)
        exec_result = executor.run(prompt)

        review_verdict = reviewer.review(
            task_description=task.description,
            acceptance_criteria=task.acceptance_criteria,
            executor_output=exec_result.output,
        )

        attempt = AttemptRecord(
            attempt_number=attempt_num,
            executor_output=exec_result.output,
            executor_success=exec_result.success,
            executor_cost_usd=exec_result.cost_usd,
            reviewer_passed=review_verdict.passed,
            reviewer_reason=review_verdict.reason,
            reviewer_issues=review_verdict.issues,
            reviewer_cost_usd=review_verdict.cost_usd,
            is_token_exhausted=exec_result.is_token_exhausted,
        )
        result.attempts.append(attempt)

        # Save attempt file
        _write_attempt_file(round_dir / f"attempt_{attempt_num}.md", attempt)

        if review_verdict.passed:
            result.final_passed = True
            break

        # If this was the last attempt and still failed → escalate
        if attempt_num == max_attempts:
            result.escalated = True
            result.escalation_reason = _build_escalation_reason(result)

    # Save audit file
    _write_audit_file(round_dir / "audit.md", result)

    return result


def _build_executor_prompt(task: TaskDefinition) -> str:
    parts = [f"## Task\n{task.description}"]
    if task.acceptance_criteria:
        parts.append(f"\n## Acceptance Criteria\n{task.acceptance_criteria}")
    if task.context_notes:
        parts.append(f"\n## Context Notes\n{task.context_notes}")
    return "\n".join(parts)


def _build_escalation_reason(result: RoundResult) -> str:
    lines = [f"Round {result.round_id} failed after {len(result.attempts)} attempt(s)."]
    for a in result.attempts:
        exhausted = " [TOKEN EXHAUSTED]" if a.is_token_exhausted else ""
        lines.append(f"\nAttempt {a.attempt_number}{exhausted}:")
        lines.append(f"  Executor success: {a.executor_success}")
        lines.append(f"  Reviewer: {'PASS' if a.reviewer_passed else 'FAIL'}")
        lines.append(f"  Reason: {a.reviewer_reason}")
        if a.reviewer_issues:
            for issue in a.reviewer_issues:
                lines.append(f"  - {issue}")
    return "\n".join(lines)


def _write_task_file(path: Path, task: TaskDefinition) -> None:
    content = f"# Task Definition\n\n## Description\n{task.description}\n"
    if task.acceptance_criteria:
        content += f"\n## Acceptance Criteria\n{task.acceptance_criteria}\n"
    if task.context_notes:
        content += f"\n## Context Notes\n{task.context_notes}\n"
    path.write_text(content)


def _write_attempt_file(path: Path, attempt: AttemptRecord) -> None:
    verdict = "PASS" if attempt.reviewer_passed else "FAIL"
    exhausted = "\n> ⚠ TOKEN EXHAUSTED" if attempt.is_token_exhausted else ""
    issues_section = ""
    if attempt.reviewer_issues:
        issues_section = "\n## Issues\n" + "\n".join(f"- {i}" for i in attempt.reviewer_issues)

    content = (
        f"# Attempt {attempt.attempt_number}{exhausted}\n\n"
        f"## Executor Output\n{attempt.executor_output}\n\n"
        f"## Reviewer Verdict: {verdict}\n{attempt.reviewer_reason}"
        f"{issues_section}\n\n"
        f"**Cost:** executor ${attempt.executor_cost_usd:.4f} | "
        f"reviewer ${attempt.reviewer_cost_usd:.4f}\n"
    )
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
        f"## Task\n{result.task.description}\n\n"
    )
    if result.escalated:
        content += f"## Escalation Reason\n```\n{result.escalation_reason}\n```\n"
    path.write_text(content)
