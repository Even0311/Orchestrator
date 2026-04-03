"""Reviewer agent — independent Claude CLI session that verifies Executor output."""
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


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


_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class ReviewerAgent:
    """Independent reviewer that spawns a fresh Claude CLI session to verify execution."""

    def __init__(self, codebase_path: Path, model: str = "sonnet"):
        self._codebase_path = codebase_path
        self._model = model

    def review(
        self,
        task: "object",        # TaskDefinition
        exec_result: "object", # ExecutorResult (carries both git_evidence and self-reported evidence)
    ) -> ReviewResult:
        """Review via independent Claude CLI session with full codebase access."""
        prompt = self._build_review_prompt(task, exec_result)

        cmd = [
            "claude",
            "-p", prompt,
            "--model", self._model,
            "--permission-mode", "bypassPermissions",
            "--output-format", "json",
            "--add-dir", str(self._codebase_path),
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self._codebase_path),
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            return ReviewResult(
                result="FAIL",
                confidence="low",
                unmet_criteria=[],
                suspicious_claims=[],
                required_fixes=["Reviewer timed out — manual review required"],
                human_review_needed=True,
                rationale="Reviewer Claude CLI session timed out after 5 minutes.",
            )
        except FileNotFoundError:
            return ReviewResult(
                result="FAIL",
                confidence="low",
                unmet_criteria=[],
                suspicious_claims=[],
                required_fixes=["Claude CLI not found"],
                human_review_needed=True,
                rationale="Claude Code CLI not found. Ensure 'claude' is installed and in PATH.",
            )

        # Parse Claude CLI JSON output
        cost = 0.0
        output_text = ""
        if proc.stdout.strip():
            try:
                data = json.loads(proc.stdout)
                output_text = data.get("result", "")
                cost = data.get("total_cost_usd", 0.0) or 0.0
            except json.JSONDecodeError:
                output_text = proc.stdout

        if not output_text:
            output_text = proc.stderr.strip() or "No output from reviewer"

        verdict = _parse_review_result(output_text)
        verdict.cost_usd = cost
        return verdict

    def _build_review_prompt(self, task: "object", exec_result: "object") -> str:
        """Build the review prompt with task info, git evidence, and instructions."""
        # Load the reviewer prompt template
        template_path = _PROMPTS_DIR / "reviewer.md"
        template = template_path.read_text() if template_path.exists() else ""

        # Task info
        criteria = getattr(task, "acceptance_criteria", [])
        required_tests = getattr(task, "required_tests", [])
        criteria_text = "\n".join(f"- {c}" for c in criteria) if criteria else "(none)"
        tests_text = "\n".join(f"- {t}" for t in required_tests) if required_tests else "(none)"

        task_section = (
            f"## Task\n"
            f"**Title:** {getattr(task, 'title', '')}\n"
            f"**Objective:** {getattr(task, 'objective', '')}\n"
            f"**Scope:** {getattr(task, 'exact_scope', '')}\n\n"
            f"### Acceptance Criteria\n{criteria_text}\n\n"
            f"### Required Tests\n{tests_text}"
        )

        # Git evidence
        git_ev = getattr(exec_result, "git_evidence", None)
        git_section = "## Git Evidence\n"
        if git_ev and not getattr(git_ev, "error", ""):
            modified = getattr(git_ev, "files_modified", [])
            added = getattr(git_ev, "files_added", [])
            deleted = getattr(git_ev, "files_deleted", [])
            diff_stat = getattr(git_ev, "diff_stat", "")
            git_section += f"Modified: {modified}\nAdded: {added}\nDeleted: {deleted}\n"
            if diff_stat:
                git_section += f"Diff stat:\n{diff_stat}\n"
        else:
            git_section += "(no git evidence available)\n"

        # Self-report (supplementary)
        self_ev = getattr(exec_result, "evidence", None)
        report_section = "## Executor Self-Report (supplementary — verify against actual code)\n"
        if self_ev:
            report_section += (
                f"Summary: {getattr(self_ev, 'summary', '')}\n"
                f"Commands run: {getattr(self_ev, 'commands_run', [])}\n"
                f"Test results: {getattr(self_ev, 'test_results', '')}\n"
                f"Unresolved: {getattr(self_ev, 'unresolved_issues', [])}\n"
            )
        else:
            report_section += "(no self-report)\n"

        return f"{template}\n\n{task_section}\n\n{git_section}\n{report_section}"


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
