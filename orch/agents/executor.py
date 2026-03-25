"""Executor agent — runs tasks via Claude Code CLI subprocess."""
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from orch.utils.evidence_collector import GitEvidence, collect_git_evidence


@dataclass
class ExecutorEvidence:
    """Self-reported evidence extracted from Executor output.

    Supplementary to GitEvidence. Use GitEvidence as the authoritative source
    for files_changed and diff information.
    """
    summary: str = ""
    files_changed: list[str] = field(default_factory=list)   # self-reported, may be incomplete
    commands_run: list[str] = field(default_factory=list)    # self-reported
    test_results: str = ""                                    # self-reported
    diff_summary: str = ""                                    # self-reported
    unresolved_issues: list[str] = field(default_factory=list)


@dataclass
class ExecutorResult:
    success: bool
    output: str
    cost_usd: float
    session_id: str
    is_token_exhausted: bool = False
    evidence: ExecutorEvidence = field(default_factory=ExecutorEvidence)
    git_evidence: GitEvidence = field(default_factory=GitEvidence)
    raw: dict | None = None


# Error patterns indicating token exhaustion
_TOKEN_EXHAUSTED_PATTERNS = (
    "claude ai usage limit",
    "usage limit reached",
    "rate limit",
    "token limit",
    "out of tokens",
    "exceeded your",
    "quota exceeded",
)

# Appended to every executor prompt to request structured self-report
_EVIDENCE_SUFFIX = """
---
After completing ALL your work above, append the following JSON block EXACTLY at the end of your response.
Replace each placeholder with what you actually did:

<evidence>
{
  "summary": "one sentence: what was accomplished",
  "files_changed": ["path/to/modified_file.py"],
  "commands_run": ["pytest tests/", "npm install"],
  "test_results": "e.g. 3 passed / 0 failed, or 'not run'",
  "diff_summary": "brief description of the key changes made",
  "unresolved_issues": []
}
</evidence>

Use empty array [] if a field has no content. Do NOT omit any field.
"""


class ExecutorAgent:
    def __init__(self, codebase_path: Path, model: str = "sonnet"):
        self._codebase_path = codebase_path
        self._model = model

    def run(self, task_prompt: str) -> ExecutorResult:
        """Run a task in the managed codebase via Claude Code CLI."""
        full_prompt = task_prompt + _EVIDENCE_SUFFIX

        cmd = [
            "claude",
            "-p", full_prompt,
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
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            result = ExecutorResult(
                success=False,
                output="Executor timed out after 10 minutes.",
                cost_usd=0.0,
                session_id="",
            )
            result.git_evidence = collect_git_evidence(self._codebase_path)
            return result
        except FileNotFoundError:
            return ExecutorResult(
                success=False,
                output="Claude Code CLI not found. Ensure 'claude' is installed and in PATH.",
                cost_usd=0.0,
                session_id="",
            )

        # Parse JSON output
        if proc.stdout.strip():
            try:
                data = json.loads(proc.stdout)
                result = _build_result(data)
                # Attach externally-collected git evidence (authoritative)
                result.git_evidence = collect_git_evidence(self._codebase_path)
                return result
            except json.JSONDecodeError:
                pass

        # Fallback: non-JSON output
        error_text = proc.stderr.strip() or proc.stdout.strip() or "Unknown error"
        result = ExecutorResult(
            success=False,
            output=error_text,
            cost_usd=0.0,
            session_id="",
            is_token_exhausted=_detect_token_exhaustion(error_text),
        )
        result.git_evidence = collect_git_evidence(self._codebase_path)
        return result


def _build_result(data: dict) -> ExecutorResult:
    is_error = data.get("is_error", False)
    output = data.get("result", "")
    cost = data.get("total_cost_usd", 0.0) or 0.0
    session_id = data.get("session_id", "")

    is_token_exhausted = False
    if is_error:
        is_token_exhausted = _detect_token_exhaustion(output)

    evidence = _extract_evidence(output)

    return ExecutorResult(
        success=not is_error,
        output=output,
        cost_usd=cost,
        session_id=session_id,
        is_token_exhausted=is_token_exhausted,
        evidence=evidence,
        raw=data,
    )


def _extract_evidence(output: str) -> ExecutorEvidence:
    """Extract self-reported evidence from the <evidence>...</evidence> block."""
    m = re.search(r"<evidence>\s*(\{.*?\})\s*</evidence>", output, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            return ExecutorEvidence(
                summary=data.get("summary", ""),
                files_changed=data.get("files_changed", []),
                commands_run=data.get("commands_run", []),
                test_results=data.get("test_results", ""),
                diff_summary=data.get("diff_summary", ""),
                unresolved_issues=data.get("unresolved_issues", []),
            )
        except json.JSONDecodeError:
            pass
    return ExecutorEvidence(summary=output[:300].strip() if output else "")


def _detect_token_exhaustion(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in _TOKEN_EXHAUSTED_PATTERNS)
