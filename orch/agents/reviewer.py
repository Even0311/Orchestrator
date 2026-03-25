"""Reviewer agent — validates Executor output using both git evidence and self-report."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from orch.agents.context import build_reviewer_system_prompt, load_reviewer_context
from orch.providers.base import LLMProvider


@dataclass
class ReviewResult:
    """Structured review verdict based on execution evidence."""
    result: str                           # "PASS" | "FAIL"
    confidence: str                       # "high" | "medium" | "low"
    unmet_criteria: list[str]
    suspicious_claims: list[str]
    required_fixes: list[str]
    human_review_needed: bool
    rationale: str
    cost_usd: float = 0.0

    @property
    def passed(self) -> bool:
        return self.result == "PASS"

    # Backward compat
    @property
    def reason(self) -> str:
        return self.rationale

    @property
    def issues(self) -> list[str]:
        return self.unmet_criteria


# Backward compat alias
ReviewVerdict = ReviewResult


class ReviewerAgent:
    def __init__(self, provider: LLMProvider, state_dir: Path):
        self._provider = provider
        self._state_dir = state_dir

    def review(
        self,
        task: "object",        # TaskDefinition
        exec_result: "object", # ExecutorResult (carries both git_evidence and self-reported evidence)
    ) -> ReviewResult:
        """Review execution result using git evidence (primary) and self-report (supplementary)."""
        context = load_reviewer_context(self._state_dir)
        system_prompt = build_reviewer_system_prompt(context)

        task_section = _format_task(task)
        evidence_section = _format_evidence(exec_result)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{task_section}\n\n"
                    f"{evidence_section}\n\n"
                    "Review the evidence against each acceptance criterion. "
                    "Trust Git-Verified evidence over Executor Self-Reported claims. "
                    "Return your verdict as JSON."
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        verdict = _parse_review_result(response.content)
        verdict.cost_usd = response.cost_usd
        return verdict


def _format_task(task: "object") -> str:
    task_id = getattr(task, "task_id", "")
    title = getattr(task, "title", "")
    objective = getattr(task, "objective", getattr(task, "description", ""))
    exact_scope = getattr(task, "exact_scope", "")
    criteria = getattr(task, "acceptance_criteria", [])
    verification = getattr(task, "verification_steps", [])

    if isinstance(criteria, list):
        criteria_text = "\n".join(f"- {c}" for c in criteria)
    else:
        criteria_text = criteria

    if isinstance(verification, list):
        verification_text = "\n".join(f"- {v}" for v in verification)
    else:
        verification_text = verification

    return (
        f"## Task Package\n"
        f"ID: {task_id}  |  Title: {title}\n"
        f"Objective: {objective}\n"
        f"Scope: {exact_scope}\n\n"
        f"### Acceptance Criteria\n{criteria_text}\n\n"
        f"### Verification Steps\n{verification_text}"
    )


def _format_evidence(exec_result: "object") -> str:
    """Format evidence with git-verified section first (authoritative), self-report second."""
    git_ev = getattr(exec_result, "git_evidence", None)
    self_ev = getattr(exec_result, "evidence", None)

    lines = ["## Execution Evidence"]

    # ── Git-Verified (authoritative) ──────────────────────────────────────────
    lines.append("\n### Git-Verified (collected externally by orchestrator)")
    if git_ev and not getattr(git_ev, "error", ""):
        has_changes = getattr(git_ev, "has_changes", False)
        lines.append(f"Has uncommitted changes: {'Yes' if has_changes else 'No'}")

        modified = getattr(git_ev, "files_modified", [])
        added = getattr(git_ev, "files_added", [])
        deleted = getattr(git_ev, "files_deleted", [])

        if modified:
            lines.append(f"Modified files: {modified}")
        if added:
            lines.append(f"New files on disk: {added}")
        if deleted:
            lines.append(f"Deleted files: {deleted}")

        diff_stat = getattr(git_ev, "diff_stat", "")
        if diff_stat:
            lines.append(f"git diff --stat:\n{_indent(diff_stat)}")
        elif not has_changes:
            lines.append("(no git changes detected)")
    elif git_ev:
        lines.append(f"(git evidence unavailable: {git_ev.error})")
    else:
        lines.append("(git evidence not collected)")

    # ── Executor Self-Reported (supplementary) ────────────────────────────────
    lines.append("\n### Executor Self-Reported (supplementary — verify against git evidence)")
    if self_ev:
        summary = getattr(self_ev, "summary", "")
        commands = getattr(self_ev, "commands_run", [])
        test_results = getattr(self_ev, "test_results", "")
        unresolved = getattr(self_ev, "unresolved_issues", [])

        if summary:
            lines.append(f"Summary: {summary}")
        if commands:
            lines.append(f"Commands run: {commands}")
        if test_results:
            lines.append(f"Test results: {test_results}")
        if unresolved:
            lines.append(f"Unresolved issues: {unresolved}")
        if not any([summary, commands, test_results]):
            lines.append("(no self-report provided)")
    else:
        lines.append("(no self-report)")

    return "\n".join(lines)


def _indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def _parse_review_result(content: str) -> ReviewResult:
    """Parse the Reviewer's JSON response."""
    cleaned = re.sub(r"```(?:json)?\s*", "", content)
    cleaned = re.sub(r"```\s*", "", cleaned)

    data = None
    try:
        data = json.loads(cleaned.strip())
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
            except json.JSONDecodeError:
                pass

    if data:
        raw_result = str(data.get("result", "")).upper()
        return ReviewResult(
            result="PASS" if raw_result.startswith("PASS") else "FAIL",
            confidence=data.get("confidence", "medium"),
            unmet_criteria=data.get("unmet_criteria", []),
            suspicious_claims=data.get("suspicious_claims", []),
            required_fixes=data.get("required_fixes", []),
            human_review_needed=bool(data.get("human_review_needed", False)),
            rationale=data.get("rationale", ""),
        )

    # Fallback: detect PASS/FAIL from plain text
    upper = content.upper()
    passed = "VERDICT: PASS" in upper or '"RESULT": "PASS"' in upper
    return ReviewResult(
        result="PASS" if passed else "FAIL",
        confidence="low",
        unmet_criteria=[],
        suspicious_claims=[],
        required_fixes=["Review response could not be parsed — manual review required"],
        human_review_needed=True,
        rationale=content.strip()[:500],
    )
