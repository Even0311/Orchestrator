"""Independent Claude CLI invocations for each agent role.

Each function cold-starts a separate Claude CLI session with role-specific
context. Agents communicate only through files — no shared context.

Replaces the old single-invocation round-driver pattern where all three
subagents shared one parent session's context.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from orch.models import (
    ContractFeedback,
    ExecutionEvidence,
    ReviewVerdict,
    TaskContract,
    Verdict,
)


@dataclass
class ClaudeInvocationResult:
    """Raw result from a single Claude Code CLI invocation."""
    success: bool
    cost_usd: float
    session_id: str
    output: str
    is_error: bool
    is_token_exhausted: bool


# ── Designer ────────────────────────────────────────────────────────────────

def invoke_designer(
    *,
    codebase_path: Path,
    round_dir: Path,
    round_id: str,
    model: str = "opus",
    timeout: int = 600,
) -> tuple[TaskContract | None, ClaudeInvocationResult]:
    """Cold-start Claude CLI as designer — reads designer_brief.md, writes task_contract.json.

    Designer sees: vision, roadmap, phase context, decisions, prior failure issues.
    Designer does NOT see: executor code, evaluator reasoning.
    """
    brief_path = round_dir / "designer_brief.md"
    prompt = (
        f"You are the Designer agent for round {round_id}.\n"
        f"\n"
        f"Read the designer brief at: designer_brief.md (in the added directory)\n"
        f"\n"
        f"Your ONLY job is to produce a `task_contract.json` file in the round directory: {round_dir}\n"
        f"\n"
        f"The contract must contain these fields:\n"
        f"  - phase_id, task_key, title, objective, exact_scope\n"
        f"  - constraints (architectural constraints)\n"
        f"  - forbidden_files (glob patterns for files that must NOT be modified)\n"
        f"  - non_goals (what is explicitly out of scope)\n"
        f"  - acceptance_criteria (each must be objectively verifiable)\n"
        f"  - review_focus (what the evaluator should pay special attention to)\n"
        f"\n"
        f"The contract tells the executor WHAT to do and WHAT NOT to touch.\n"
        f"Do NOT prescribe HOW to implement — the executor decides that.\n"
        f"\n"
        f"Do NOT modify any source code or SOT files. Only write task_contract.json."
    )

    invocation = _invoke_claude(
        codebase_path=codebase_path,
        add_dir=round_dir,
        prompt=prompt,
        model=model,
        timeout=timeout,
        allowed_tools="Read,Write",
    )

    # Parse task contract
    contract_path = round_dir / "task_contract.json"
    if contract_path.exists():
        try:
            data = json.loads(contract_path.read_text())
            return TaskContract.from_dict(data), invocation
        except (json.JSONDecodeError, KeyError):
            pass

    return None, invocation


# ── Evaluator: Contract Review ──────────────────────────────────────────────

def invoke_evaluator_contract_review(
    *,
    round_dir: Path,
    round_id: str,
    model: str = "sonnet",
    timeout: int = 300,
) -> tuple[ContractFeedback | None, ClaudeInvocationResult]:
    """Cold-start Claude CLI as evaluator in contract review mode.

    Evaluator sees: acceptance_criteria and review_focus from the proposed contract.
    Evaluator does NOT see: vision, roadmap, designer reasoning.
    """
    prompt = (
        f"You are the Evaluator agent reviewing a proposed contract for round {round_id}.\n"
        f"\n"
        f"Read the evaluator contract brief at: evaluator_contract_brief.md (in the added directory)\n"
        f"\n"
        f"Your ONLY job is to assess whether each acceptance criterion is objectively verifiable\n"
        f"after code changes are made. You will later need to judge PASS/FAIL based on these criteria.\n"
        f"\n"
        f"Write `contract_feedback.json` to the round directory: {round_dir}\n"
        f"with fields: can_evaluate, cannot_evaluate, suggested_changes, needs_revision\n"
        f"\n"
        f"IMPORTANT: Set needs_revision=true ONLY when criteria are genuinely impossible to\n"
        f"verify objectively. Minor imprecisions that you can still reasonably judge do NOT\n"
        f"warrant a revision request. Revision rounds are expensive — only request one when\n"
        f"you truly cannot evaluate the criteria as written.\n"
        f"\n"
        f"Do NOT modify any other files."
    )

    invocation = _invoke_claude(
        codebase_path=None,
        add_dir=round_dir,
        prompt=prompt,
        model=model,
        timeout=timeout,
        allowed_tools="Read,Write",
    )

    feedback_path = round_dir / "contract_feedback.json"
    if feedback_path.exists():
        try:
            data = json.loads(feedback_path.read_text())
            return ContractFeedback.from_dict(data), invocation
        except (json.JSONDecodeError, KeyError):
            pass

    return None, invocation


# ── Executor ────────────────────────────────────────────────────────────────

def invoke_executor(
    *,
    codebase_path: Path,
    round_dir: Path,
    round_id: str,
    model: str = "sonnet",
    timeout: int = 1800,
) -> tuple[ExecutionEvidence | None, ClaudeInvocationResult]:
    """Cold-start Claude CLI as executor — reads task contract, writes code + evidence.

    Executor sees: task_contract.json (finalized) + full source code access.
    Executor does NOT see: designer reasoning, vision, evaluator feedback.
    """
    prompt = (
        f"You are the Executor agent for round {round_id}.\n"
        f"\n"
        f"Read the executor brief at: executor_brief.md (in the added directory)\n"
        f"It contains the finalized task contract with all requirements.\n"
        f"\n"
        f"Your job:\n"
        f"1. Read and understand the relevant source code\n"
        f"2. Implement the changes described in the contract\n"
        f"3. Write/update tests as needed\n"
        f"4. Run the test suite to verify no regressions\n"
        f"5. Write `execution_evidence.json` to: {round_dir}\n"
        f"   with fields: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues\n"
        f"\n"
        f"IMPORTANT: Do NOT modify files listed as forbidden in the contract.\n"
        f"Do NOT modify vision.md, road_map.md, decisions.md, or any orchestrator SOT files.\n"
        f"Do NOT modify CLAUDE.md or .claude/agents/ files."
    )

    invocation = _invoke_claude(
        codebase_path=codebase_path,
        add_dir=round_dir,
        prompt=prompt,
        model=model,
        timeout=timeout,
        allowed_tools="Read,Write,Bash",
        verbose=True,
    )

    evidence_path = round_dir / "execution_evidence.json"
    if evidence_path.exists():
        try:
            data = json.loads(evidence_path.read_text())
            return ExecutionEvidence.from_dict(data), invocation
        except (json.JSONDecodeError, KeyError):
            pass

    return None, invocation


# ── Evaluator: Code Review ──────────────────────────────────────────────────

def invoke_evaluator(
    *,
    codebase_path: Path,
    round_dir: Path,
    round_id: str,
    model: str = "sonnet",
    timeout: int = 600,
) -> tuple[ReviewVerdict | None, ClaudeInvocationResult]:
    """Cold-start Claude CLI as evaluator in code review mode.

    Evaluator sees: git diff + acceptance_criteria + review_focus.
    Evaluator does NOT see: executor reasoning, designer reasoning, vision.
    """
    prompt = (
        f"You are the Evaluator agent reviewing code changes for round {round_id}.\n"
        f"\n"
        f"Read the evaluator review brief at: evaluator_review_brief.md (in the added directory)\n"
        f"It contains the acceptance criteria, review focus items, and the git diff.\n"
        f"\n"
        f"Your job:\n"
        f"1. Check each acceptance criterion against the actual code changes\n"
        f"2. Pay special attention to review focus items\n"
        f"3. If existing test files were modified, examine whether the modifications are justified\n"
        f"4. Run the test suite if needed to verify\n"
        f"\n"
        f"Write `review_verdict.json` to: {round_dir}\n"
        f"with fields: verdict (PASS/FAIL/REVISION_REQUIRED), confidence, met_criteria,\n"
        f"unmet_criteria, blocker_fixes, non_blocking_suggestions, rationale\n"
        f"\n"
        f"Be independent and critical. Do NOT assume the code is correct just because tests pass.\n"
        f"Do NOT modify any source code files."
    )

    invocation = _invoke_claude(
        codebase_path=codebase_path,
        add_dir=round_dir,
        prompt=prompt,
        model=model,
        timeout=timeout,
        allowed_tools="Read,Write,Bash",
    )

    verdict_path = round_dir / "review_verdict.json"
    if verdict_path.exists():
        try:
            data = json.loads(verdict_path.read_text())
            return ReviewVerdict.from_dict(data), invocation
        except (json.JSONDecodeError, KeyError):
            pass

    return None, invocation


# ── Shared CLI Invocation ───────────────────────────────────────────────────

def _invoke_claude(
    *,
    codebase_path: Path | None,
    add_dir: Path,
    prompt: str,
    model: str,
    timeout: int,
    allowed_tools: str = "Read,Write",
    verbose: bool = False,
) -> ClaudeInvocationResult:
    """Invoke Claude Code CLI as a subprocess.

    Each invocation is a cold start — no shared context with other invocations.
    When verbose=True, streams stderr to the terminal in real time so the
    operator can see what the agent is doing.
    """
    cmd = [
        "claude",
        "-p", prompt,
        "--allowedTools", allowed_tools,
        "--model", model,
        "--permission-mode", "bypassPermissions",
        "--output-format", "json",
        "--add-dir", str(add_dir),
    ]

    cwd = str(codebase_path) if codebase_path else str(add_dir)

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if not verbose else None,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return ClaudeInvocationResult(
                success=False, cost_usd=0.0, session_id="",
                output=f"Claude CLI timed out after {timeout}s.",
                is_error=True, is_token_exhausted=False,
            )
    except FileNotFoundError:
        return ClaudeInvocationResult(
            success=False, cost_usd=0.0, session_id="",
            output="Claude Code CLI not found. Ensure 'claude' is installed and in PATH.",
            is_error=True, is_token_exhausted=False,
        )

    # Parse JSON output from Claude CLI
    stderr = stderr or ""
    raw = stdout.strip() or stderr.strip() or ""
    cost = 0.0
    session_id = ""
    result_text = raw
    is_error = False

    if stdout.strip():
        try:
            data = json.loads(stdout)
            result_text = data.get("result", "")
            cost = data.get("total_cost_usd", 0.0) or 0.0
            session_id = data.get("session_id", "")
            is_error = bool(data.get("is_error", False))
        except json.JSONDecodeError:
            # Log first 500 chars of stdout for debugging
            import sys
            preview = stdout.strip()[:500]
            print(f"  ⚠ Claude JSON parse failed. stdout preview: {preview!r}", file=sys.stderr)

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
