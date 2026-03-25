"""Executor agent — runs tasks via Claude Code CLI subprocess."""
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutorResult:
    success: bool
    output: str
    cost_usd: float
    session_id: str
    is_token_exhausted: bool = False
    raw: dict | None = None


# Error message patterns that indicate token exhaustion
_TOKEN_EXHAUSTED_PATTERNS = (
    "claude ai usage limit",
    "usage limit reached",
    "rate limit",
    "token limit",
    "out of tokens",
    "exceeded your",
    "quota exceeded",
)


class ExecutorAgent:
    def __init__(self, codebase_path: Path, model: str = "sonnet"):
        self._codebase_path = codebase_path
        self._model = model

    def run(self, task_prompt: str) -> ExecutorResult:
        """Run a task in the managed codebase via Claude Code CLI."""
        cmd = [
            "claude",
            "-p", task_prompt,
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
                timeout=600,  # 10 min max per task
            )
        except subprocess.TimeoutExpired:
            return ExecutorResult(
                success=False,
                output="Executor timed out after 10 minutes.",
                cost_usd=0.0,
                session_id="",
            )
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
                return _build_result(data)
            except json.JSONDecodeError:
                pass

        # Fallback: non-JSON output or stderr
        error_text = proc.stderr.strip() or proc.stdout.strip() or "Unknown error"
        return ExecutorResult(
            success=False,
            output=error_text,
            cost_usd=0.0,
            session_id="",
            is_token_exhausted=_detect_token_exhaustion(error_text),
        )


def _build_result(data: dict) -> ExecutorResult:
    is_error = data.get("is_error", False)
    output = data.get("result", "")
    cost = data.get("total_cost_usd", 0.0) or 0.0
    session_id = data.get("session_id", "")

    is_token_exhausted = False
    if is_error:
        is_token_exhausted = _detect_token_exhaustion(output)

    return ExecutorResult(
        success=not is_error,
        output=output,
        cost_usd=cost,
        session_id=session_id,
        is_token_exhausted=is_token_exhausted,
        raw=data,
    )


def _detect_token_exhaustion(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in _TOKEN_EXHAUSTED_PATTERNS)
