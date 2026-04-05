"""Single-invocation Claude Code round driver.

Orchestrator calls `run_attempt()` once per attempt.  Claude Code internally
coordinates designer → executor → reviewer via repo-local subagent definitions.
Artifacts are exchanged via files in the round directory.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from orch.briefing import read_artifacts
from orch.models import (
    AttemptRecord,
    ExecutionEvidence,
    ReviewVerdict,
    TaskContract,
    Verdict,
)
from orch.utils.evidence_collector import GitEvidence, collect_git_evidence


@dataclass
class ClaudeInvocationResult:
    """Raw result from a single Claude Code CLI invocation."""
    success: bool
    cost_usd: float
    session_id: str
    output: str
    is_error: bool
    is_token_exhausted: bool


def subagents_available(codebase_path: Path) -> bool:
    """Check if the target repo has the required subagent definitions."""
    agents_dir = codebase_path / ".claude" / "agents"
    return all(
        (agents_dir / name).exists()
        for name in ("designer.md", "executor.md", "reviewer.md", "round-driver.md")
    )


def run_attempt(
    *,
    codebase_path: Path,
    round_dir: Path,
    round_id: str,
    attempt_num: int,
    model: str = "sonnet",
    timeout: int = 900,
) -> AttemptRecord:
    """Run a single Claude Code invocation for one round attempt.

    The round_dir must already contain round_brief.md (written by orchestrator).
    Claude reads it via --add-dir and writes artifact files back to round_dir.
    """
    prompt = _build_driver_prompt(round_id=round_id, attempt_num=attempt_num, round_dir=round_dir)

    invocation = _invoke_claude(
        codebase_path=codebase_path,
        round_dir=round_dir,
        prompt=prompt,
        model=model,
        timeout=timeout,
    )

    # Collect git evidence (authoritative, independent of Claude's self-report)
    git_evidence = collect_git_evidence(codebase_path)

    # Read artifact files that Claude wrote
    artifacts = read_artifacts(round_dir)

    # Parse task contract
    task_data = artifacts.get("task_contract")
    if task_data:
        task = TaskContract.from_dict(task_data)
    else:
        task = TaskContract(
            phase_id="", task_key=round_id,
            title="(task contract not produced)",
            objective="(Claude did not write task_contract.json)",
        )

    # Parse execution evidence
    exec_data = artifacts.get("execution_evidence")
    if exec_data:
        execution = ExecutionEvidence.from_dict(exec_data)
    else:
        execution = ExecutionEvidence(summary=invocation.output[:300])

    # Parse review verdict
    review_data = artifacts.get("review_verdict")
    if review_data:
        review = ReviewVerdict.from_dict(review_data)
    else:
        review = ReviewVerdict(
            verdict=Verdict.FAIL,
            confidence="low",
            rationale="No review_verdict.json produced by Claude.",
            blocker_fixes=["review_verdict.json not found in round directory"],
        )

    return AttemptRecord(
        attempt_number=attempt_num,
        task=task,
        execution_evidence=execution,
        git_evidence=git_evidence,
        review_verdict=review,
        claude_cost_usd=invocation.cost_usd,
        is_token_exhausted=invocation.is_token_exhausted,
        claude_output=invocation.output,
    )


def _build_driver_prompt(*, round_id: str, attempt_num: int, round_dir: Path) -> str:
    """Build the prompt passed to Claude via -p flag."""
    return (
        f"Execute round {round_id}, attempt {attempt_num}.\n"
        f"Follow the mandatory process defined in your agent instructions.\n"
        f"\n"
        f"Read the round brief at: round_brief.md (in the added directory)\n"
        f"The round directory path is: {round_dir}\n"
        f"\n"
        f"After all subagents finish, ensure these artifact files exist in the round directory:\n"
        f"  - task_contract.json\n"
        f"  - execution_evidence.json\n"
        f"  - review_verdict.json\n"
        f"\n"
        f"Do NOT modify vision.md, road_map.md, decisions.md, or any orchestrator SOT files."
    )


def _invoke_claude(
    *,
    codebase_path: Path,
    round_dir: Path,
    prompt: str,
    model: str,
    timeout: int,
) -> ClaudeInvocationResult:
    """Invoke Claude Code CLI as a subprocess."""
    cmd = [
        "claude",
        "-p", prompt,
        "--agent", "round-driver",
        "--allowedTools", "Agent,Read,Write",
        "--model", model,
        "--permission-mode", "bypassPermissions",
        "--output-format", "json",
        "--add-dir", str(round_dir),
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(codebase_path),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ClaudeInvocationResult(
            success=False, cost_usd=0.0, session_id="",
            output=f"Claude round driver timed out after {timeout}s.",
            is_error=True, is_token_exhausted=False,
        )
    except FileNotFoundError:
        return ClaudeInvocationResult(
            success=False, cost_usd=0.0, session_id="",
            output="Claude Code CLI not found. Ensure 'claude' is installed and in PATH.",
            is_error=True, is_token_exhausted=False,
        )

    # Parse JSON output from Claude CLI
    raw = proc.stdout.strip() or proc.stderr.strip() or ""
    cost = 0.0
    session_id = ""
    result_text = raw
    is_error = False

    if proc.stdout.strip():
        try:
            data = json.loads(proc.stdout)
            result_text = data.get("result", "")
            cost = data.get("total_cost_usd", 0.0) or 0.0
            session_id = data.get("session_id", "")
            is_error = bool(data.get("is_error", False))
        except json.JSONDecodeError:
            pass

    return ClaudeInvocationResult(
        success=not is_error,
        cost_usd=cost,
        session_id=session_id,
        output=result_text,
        is_error=is_error,
        is_token_exhausted=_detect_token_exhaustion(result_text) if is_error else False,
    )


def _detect_token_exhaustion(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in (
        "claude ai usage limit",
        "usage limit reached",
        "rate limit",
        "token limit",
        "out of tokens",
        "quota exceeded",
    ))
