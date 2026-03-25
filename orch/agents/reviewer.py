"""Reviewer agent — validates Executor output against task definition."""
from dataclasses import dataclass
from pathlib import Path

from orch.agents.context import build_reviewer_system_prompt, load_project_context
from orch.providers.base import LLMProvider


@dataclass
class ReviewVerdict:
    passed: bool
    reason: str
    issues: list[str]
    cost_usd: float = 0.0


class ReviewerAgent:
    def __init__(self, provider: LLMProvider, state_dir: Path):
        self._provider = provider
        self._state_dir = state_dir

    def review(
        self,
        task_description: str,
        acceptance_criteria: str,
        executor_output: str,
    ) -> ReviewVerdict:
        """Review the Executor's output and return a verdict."""
        context = load_project_context(self._state_dir)
        system_prompt = build_reviewer_system_prompt(context)

        messages = [
            {
                "role": "user",
                "content": (
                    f"## Task Definition\n{task_description}\n\n"
                    f"## Acceptance Criteria\n{acceptance_criteria}\n\n"
                    f"## Executor Output\n{executor_output}\n\n"
                    "Review the output against the task and acceptance criteria. "
                    "Return your verdict in the required format."
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        verdict = _parse_verdict(response.content)
        verdict.cost_usd = response.cost_usd
        return verdict


def _parse_verdict(content: str) -> ReviewVerdict:
    """Parse VERDICT / REASON / ISSUES from the Reviewer's response."""
    passed = False
    reason = ""
    issues: list[str] = []

    current_section = None
    reason_lines: list[str] = []
    issues_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        upper = stripped.upper()

        if upper.startswith("VERDICT:"):
            verdict_value = stripped[8:].strip().upper()
            passed = verdict_value.startswith("PASS")
        elif upper.startswith("REASON:"):
            current_section = "reason"
            remainder = stripped[7:].strip()
            if remainder:
                reason_lines.append(remainder)
        elif upper.startswith("ISSUES:"):
            current_section = "issues"
            remainder = stripped[7:].strip()
            if remainder and remainder.upper() != "NONE":
                issues_lines.append(remainder)
        elif current_section == "reason":
            reason_lines.append(line)
        elif current_section == "issues":
            if stripped and stripped.upper() != "NONE":
                issues_lines.append(stripped)

    reason = " ".join(reason_lines).strip()
    issues = [i.lstrip("-•* ").strip() for i in issues_lines if i.strip()]

    # Fallback if parsing failed
    if not reason:
        reason = content.strip()

    return ReviewVerdict(passed=passed, reason=reason, issues=issues)
