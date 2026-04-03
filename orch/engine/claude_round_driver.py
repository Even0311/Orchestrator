"""Single-entry Claude Code round driver that delegates work to repo-local subagents."""
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from orch.agents.designer import TaskDefinition
from orch.agents.executor import ExecutorEvidence, ExecutorResult
from orch.agents.reviewer import ReviewResult
from orch.utils.evidence_collector import collect_git_evidence


@dataclass
class ClaudeDrivenRoundAttempt:
    task: TaskDefinition
    exec_result: ExecutorResult
    review_result: ReviewResult


def subagents_available(codebase_path: Path) -> bool:
    agents_dir = codebase_path / ".claude" / "agents"
    return all((agents_dir / name).exists() for name in ("designer.md", "executor.md", "reviewer.md"))


def inject_round_driver_context(codebase_path: Path, instruction: str, prior_failure: str = "") -> None:
    runtime_dir = codebase_path / ".orch" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "current_round_instruction.md").write_text(instruction)
    if prior_failure:
        (runtime_dir / "prior_failure.md").write_text(prior_failure)
    else:
        prior = runtime_dir / "prior_failure.md"
        if prior.exists():
            prior.unlink()


def run_attempt(
    *,
    codebase_path: Path,
    round_id: str,
    attempt_num: int,
    model: str,
) -> ClaudeDrivenRoundAttempt:
    prompt = _build_driver_prompt(round_id=round_id, attempt_num=attempt_num)
    cmd = [
        "claude",
        "-p", prompt,
        "--model", model,
        "--permission-mode", "bypassPermissions",
        "--output-format", "json",
        "--add-dir", str(codebase_path),
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(codebase_path),
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        return _timeout_attempt(codebase_path)
    except FileNotFoundError:
        return _missing_claude_attempt(codebase_path)

    raw_cli = proc.stdout.strip() or proc.stderr.strip() or ""
    is_error = False
    cost = 0.0
    session_id = ""
    result_text = raw_cli
    if proc.stdout.strip():
        try:
            data = json.loads(proc.stdout)
            result_text = data.get("result", "")
            cost = data.get("total_cost_usd", 0.0) or 0.0
            session_id = data.get("session_id", "")
            is_error = bool(data.get("is_error", False))
        except json.JSONDecodeError:
            pass

    payload = _extract_payload(result_text)
    task = _parse_task(payload)
    exec_evidence = _parse_execution(payload)
    review = _parse_review(payload)

    exec_result = ExecutorResult(
        success=not is_error,
        output=result_text,
        cost_usd=cost,
        session_id=session_id,
        is_token_exhausted=_detect_token_exhaustion(result_text) if is_error else False,
        evidence=exec_evidence,
        git_evidence=collect_git_evidence(codebase_path),
        raw=payload if payload else None,
    )
    return ClaudeDrivenRoundAttempt(task=task, exec_result=exec_result, review_result=review)


def _build_driver_prompt(*, round_id: str, attempt_num: int) -> str:
    return f"""
You are the top-level round driver for this repository.
This repository contains project-level Claude Code subagents named: designer, executor, reviewer.
For this attempt, you should use those subagents as the internal roles for planning, implementation, and review.

Read these repo-local files first:
- .orch/current_phase.md
- .orch/context/designer.md
- .orch/runtime/current_round_instruction.md
- .orch/runtime/recent_rounds.md if it exists
- .orch/runtime/prior_failure.md if it exists

Process for round {round_id}, attempt {attempt_num}:
1. Use the designer subagent to derive the concrete task for this attempt.
2. Use the executor subagent to implement that task in the actual codebase.
3. Use the reviewer subagent to review the actual implementation against the task.
4. Return ONLY one JSON object matching the schema below.
5. Do not update vision.md or roadmap.md.
6. Do not update source-of-truth docs in this command; this command is only for task/execution/review.

Required JSON schema:
{{
  "task": {{
    "task_id": "{round_id}",
    "title": "short title",
    "objective": "concrete objective",
    "exact_scope": "precise boundaries",
    "constraints": ["constraint 1"],
    "acceptance_criteria": ["criterion 1"],
    "required_tests": ["test expectation 1"],
    "non_goals": ["non-goal 1"]
  }},
  "execution": {{
    "summary": "one sentence summary",
    "files_changed": ["path/to/file.py"],
    "commands_run": ["pytest -q"],
    "test_results": "summary string or not run",
    "diff_summary": "brief diff summary",
    "unresolved_issues": []
  }},
  "review": {{
    "result": "PASS or FAIL",
    "confidence": "high | medium | low",
    "unmet_criteria": [],
    "suspicious_claims": [],
    "required_fixes": [],
    "human_review_needed": false,
    "rationale": "brief justification"
  }}
}}
""".strip()


def _extract_payload(text: str) -> dict | None:
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = re.sub(r"```\s*", "", cleaned)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "task" in data:
            return data
    except Exception:
        pass

    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _parse_task(payload: dict | None) -> TaskDefinition:
    task = (payload or {}).get("task", {}) if payload else {}
    return TaskDefinition(
        task_id=task.get("task_id", ""),
        title=task.get("title", ""),
        objective=task.get("objective", ""),
        exact_scope=task.get("exact_scope", ""),
        acceptance_criteria=task.get("acceptance_criteria", []) or [],
        verification_steps=[],
        non_goals=task.get("non_goals", []) or [],
        likely_files=[],
        constraints=task.get("constraints", []) or [],
        required_tests=task.get("required_tests", []) or [],
    )


def _parse_execution(payload: dict | None) -> ExecutorEvidence:
    execution = (payload or {}).get("execution", {}) if payload else {}
    return ExecutorEvidence(
        summary=execution.get("summary", ""),
        files_changed=execution.get("files_changed", []) or [],
        commands_run=execution.get("commands_run", []) or [],
        test_results=execution.get("test_results", ""),
        diff_summary=execution.get("diff_summary", ""),
        unresolved_issues=execution.get("unresolved_issues", []) or [],
    )


def _parse_review(payload: dict | None) -> ReviewResult:
    review = (payload or {}).get("review", {}) if payload else {}
    result = str(review.get("result", "FAIL")).upper()
    return ReviewResult(
        result="PASS" if result.startswith("PASS") else "FAIL",
        confidence=review.get("confidence", "low"),
        unmet_criteria=review.get("unmet_criteria", []) or [],
        suspicious_claims=review.get("suspicious_claims", []) or [],
        required_fixes=review.get("required_fixes", []) or ["review output missing or invalid"],
        human_review_needed=bool(review.get("human_review_needed", False)),
        rationale=review.get("rationale", "No valid review rationale returned."),
        cost_usd=0.0,
    )


def _timeout_attempt(codebase_path: Path) -> ClaudeDrivenRoundAttempt:
    return ClaudeDrivenRoundAttempt(
        task=TaskDefinition(task_id="", title="", objective="", exact_scope="", acceptance_criteria=[], verification_steps=[], non_goals=[]),
        exec_result=ExecutorResult(
            success=False,
            output="Claude round driver timed out after 15 minutes.",
            cost_usd=0.0,
            session_id="",
            is_token_exhausted=False,
            evidence=ExecutorEvidence(summary="Claude round driver timed out."),
            git_evidence=collect_git_evidence(codebase_path),
            raw=None,
        ),
        review_result=ReviewResult(
            result="FAIL",
            confidence="low",
            unmet_criteria=[],
            suspicious_claims=[],
            required_fixes=["Claude round driver timed out"],
            human_review_needed=True,
            rationale="Claude round driver timed out after 15 minutes.",
        ),
    )


def _missing_claude_attempt(codebase_path: Path) -> ClaudeDrivenRoundAttempt:
    return ClaudeDrivenRoundAttempt(
        task=TaskDefinition(task_id="", title="", objective="", exact_scope="", acceptance_criteria=[], verification_steps=[], non_goals=[]),
        exec_result=ExecutorResult(
            success=False,
            output="Claude Code CLI not found. Ensure 'claude' is installed and in PATH.",
            cost_usd=0.0,
            session_id="",
            is_token_exhausted=False,
            evidence=ExecutorEvidence(summary="Claude Code CLI not found."),
            git_evidence=collect_git_evidence(codebase_path),
            raw=None,
        ),
        review_result=ReviewResult(
            result="FAIL",
            confidence="low",
            unmet_criteria=[],
            suspicious_claims=[],
            required_fixes=["Claude Code CLI not found"],
            human_review_needed=True,
            rationale="Claude Code CLI not found. Ensure 'claude' is installed and in PATH.",
        ),
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
