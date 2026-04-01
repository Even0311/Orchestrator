"""Executes a single Round: Designer → Executor → [Designer repair →] Executor → Reviewer."""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from orch.agents.designer import DesignerAgent, TaskDefinition
from orch.agents.executor import ExecutorAgent, ExecutorEvidence, ExecutorResult
from orch.agents.reviewer import ReviewerAgent, ReviewResult
from orch.utils.evidence_collector import GitEvidence
from orch.utils.verification_runner import VerificationResults, run_verification_steps


@dataclass
class AttemptRecord:
    attempt_number: int
    task_used: TaskDefinition          # may differ from round's initial task (repair)
    executor_output: str
    executor_evidence: ExecutorEvidence   # self-reported
    executor_git_evidence: GitEvidence    # externally collected (authoritative)
    executor_success: bool
    executor_cost_usd: float
    reviewer_result: str               # "PASS" | "FAIL"
    reviewer_confidence: str
    reviewer_rationale: str
    reviewer_unmet_criteria: list[str]
    reviewer_required_fixes: list[str]
    reviewer_human_review_needed: bool
    reviewer_cost_usd: float
    verification_results: VerificationResults | None = None
    is_token_exhausted: bool = False

    # Backward compat
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
    task: TaskDefinition              # initial task from Designer
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
    max_attempts: int = 2,
) -> RoundResult:
    """Run a complete round. Returns the result regardless of pass/fail."""

    round_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Designer plans the initial task
    task = designer.plan_next_task(instruction, round_id)
    result = RoundResult(
        round_id=round_id,
        task=task,
        designer_cost_usd=task.cost_usd,
    )

    # Save initial task package
    _write_task_files(round_dir, task, prefix="task")

    current_task = task  # may be replaced by repair on FAIL

    # Step 2: Executor + Reviewer loop (up to max_attempts)
    for attempt_num in range(1, max_attempts + 1):
        prompt = _build_executor_prompt(current_task)
        exec_result = executor.run(prompt)

        # Run mechanical verification (Designer's verification_steps)
        verification = None
        if codebase_path and current_task.verification_steps:
            verification = run_verification_steps(
                steps=current_task.verification_steps,
                cwd=codebase_path,
            )

        # Save execution report (git-verified + mechanical verification + self-reported)
        _write_execution_report(
            round_dir / f"execution_report_attempt_{attempt_num}.json",
            attempt_num, exec_result, verification,
        )

        # Reviewer evaluates using full exec_result + mechanical verification
        review_verdict = reviewer.review(
            task=current_task,
            exec_result=exec_result,
            verification_results=verification,
        )

        # Save review result
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

        # Save human-readable attempt summary
        _write_attempt_file(round_dir / f"attempt_{attempt_num}.md", attempt)

        if review_verdict.passed:
            result.final_passed = True
            break

        # Not passed — decide what to do next
        if attempt_num < max_attempts:
            # Designer repair step: produce targeted fix task based on review failures
            repaired = designer.repair_task(current_task, review_verdict, exec_result.evidence)
            result.repair_cost_usd += repaired.cost_usd
            current_task = repaired
            _write_task_files(round_dir, repaired, prefix=f"repaired_task_attempt_{attempt_num + 1}")
        else:
            # Max attempts reached — escalate
            result.escalated = True
            result.escalation_reason = _build_escalation_reason(result)

    # Save audit file
    _write_audit_file(round_dir / "audit.md", result)

    return result


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_executor_prompt(task: TaskDefinition) -> str:
    criteria = "\n".join(f"- {c}" for c in task.acceptance_criteria)
    verification = "\n".join(f"- {v}" for v in task.verification_steps)
    non_goals = "\n".join(f"- {g}" for g in task.non_goals)
    constraints = "\n".join(f"- {c}" for c in task.constraints)
    likely_files = "\n".join(f"- {f}" for f in task.likely_files)

    parts = [
        f"# Task: {task.title}",
        f"\n## Objective\n{task.objective}",
        f"\n## Exact Scope\n{task.exact_scope}",
    ]
    if likely_files:
        parts.append(f"\n## Likely Files\n{likely_files}")
    if constraints:
        parts.append(f"\n## Constraints\n{constraints}")
    if criteria:
        parts.append(f"\n## Acceptance Criteria\n{criteria}")
    if verification:
        parts.append(f"\n## Verification Steps\n{verification}")
    if non_goals:
        parts.append(f"\n## Non-Goals (Do NOT do these)\n{non_goals}")

    return "\n".join(parts)


# ── File writers ──────────────────────────────────────────────────────────────

def _write_task_files(round_dir: Path, task: TaskDefinition, prefix: str) -> None:
    """Write task.json and task.md (or repaired_task_attempt_N.json/md)."""
    data = {
        "task_id": task.task_id,
        "title": task.title,
        "objective": task.objective,
        "exact_scope": task.exact_scope,
        "likely_files": task.likely_files,
        "constraints": task.constraints,
        "acceptance_criteria": task.acceptance_criteria,
        "verification_steps": task.verification_steps,
        "non_goals": task.non_goals,
    }
    (round_dir / f"{prefix}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

    criteria = "\n".join(f"- {c}" for c in task.acceptance_criteria)
    verification = "\n".join(f"- {v}" for v in task.verification_steps)
    non_goals = "\n".join(f"- {g}" for g in task.non_goals)
    md = (
        f"# Task: {task.title}\n\n"
        f"**ID:** {task.task_id}  \n"
        f"**Objective:** {task.objective}\n\n"
        f"**Exact Scope:** {task.exact_scope}\n\n"
    )
    if task.likely_files:
        md += f"## Likely Files\n" + "\n".join(f"- {f}" for f in task.likely_files) + "\n\n"
    if task.constraints:
        md += f"## Constraints\n" + "\n".join(f"- {c}" for c in task.constraints) + "\n\n"
    if criteria:
        md += f"## Acceptance Criteria\n{criteria}\n\n"
    if verification:
        md += f"## Verification Steps\n{verification}\n\n"
    if non_goals:
        md += f"## Non-Goals\n{non_goals}\n"
    (round_dir / f"{prefix}.md").write_text(md)


def _write_execution_report(
    path: Path, attempt_num: int, exec_result: ExecutorResult,
    verification: VerificationResults | None = None,
) -> None:
    ev = exec_result.evidence
    git_ev = exec_result.git_evidence
    data = {
        "attempt": attempt_num,
        "success": exec_result.success,
        "cost_usd": exec_result.cost_usd,
        "is_token_exhausted": exec_result.is_token_exhausted,
        # Git-collected evidence is listed first — it's the authoritative source
        "git_evidence": {
            "files_modified": git_ev.files_modified,
            "files_added": git_ev.files_added,
            "files_deleted": git_ev.files_deleted,
            "diff_stat": git_ev.diff_stat,
            "diff_patch_truncated": git_ev.diff_patch_truncated,
            "has_changes": git_ev.has_changes,
            "error": git_ev.error,
        },
        # Mechanical verification — orchestrator-run verification_steps
        "mechanical_verification": None,
        # Self-reported by Executor — supplementary
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
        data["mechanical_verification"] = {
            "summary": verification.summary,
            "all_passed": verification.all_passed,
            "steps": [
                {
                    "command": s.command,
                    "exit_code": s.exit_code,
                    "passed": s.passed,
                    "stdout": s.stdout,
                    "stderr": s.stderr,
                }
                for s in verification.steps
            ],
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
    git_ev = attempt.executor_evidence  # access via the record; git ev is in exec report
    verdict = attempt.reviewer_result
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
        f"## Reviewer Verdict: {verdict} (confidence: {attempt.reviewer_confidence})\n"
        f"{attempt.reviewer_rationale}\n\n"
        f"**Cost:** executor ${attempt.executor_cost_usd:.4f} | "
        f"reviewer ${attempt.reviewer_cost_usd:.4f}\n"
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
