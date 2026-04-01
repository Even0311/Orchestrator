"""Mechanical verification: run Designer's verification_steps and report objective pass/fail."""
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VerificationStepResult:
    command: str
    exit_code: int
    stdout: str       # truncated to MAX_OUTPUT chars
    stderr: str       # truncated to MAX_OUTPUT chars
    passed: bool      # exit_code == 0

    MAX_OUTPUT: int = 500


@dataclass
class VerificationResults:
    """Aggregate result of running all verification_steps."""
    steps: list[VerificationStepResult] = field(default_factory=list)
    all_passed: bool = False
    summary: str = ""                # e.g. "5/6 passed"
    error: str = ""                  # non-empty if runner itself failed


def run_verification_steps(
    steps: list[str],
    cwd: Path,
    timeout_per_step: int = 10,
) -> VerificationResults:
    """Execute each verification command in the target codebase and collect results.

    Commands run with shell=True because Designer writes shell constructs (pipes, etc.).
    Each command runs in its own subprocess — no shared state between steps.
    """
    if not steps:
        return VerificationResults(
            all_passed=True,
            summary="0/0 passed (no verification steps)",
        )

    if not cwd.exists():
        return VerificationResults(error=f"cwd does not exist: {cwd}")

    results: list[VerificationStepResult] = []

    for cmd in steps:
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout_per_step,
            )
            step = VerificationStepResult(
                command=cmd,
                exit_code=proc.returncode,
                stdout=proc.stdout[:VerificationStepResult.MAX_OUTPUT] if proc.stdout else "",
                stderr=proc.stderr[:VerificationStepResult.MAX_OUTPUT] if proc.stderr else "",
                passed=(proc.returncode == 0),
            )
        except subprocess.TimeoutExpired:
            step = VerificationStepResult(
                command=cmd,
                exit_code=-1,
                stdout="",
                stderr=f"TIMEOUT after {timeout_per_step}s",
                passed=False,
            )
        except Exception as e:
            step = VerificationStepResult(
                command=cmd,
                exit_code=-1,
                stdout="",
                stderr=str(e)[:VerificationStepResult.MAX_OUTPUT],
                passed=False,
            )
        results.append(step)

    passed_count = sum(1 for s in results if s.passed)
    total = len(results)

    return VerificationResults(
        steps=results,
        all_passed=(passed_count == total),
        summary=f"{passed_count}/{total} passed",
    )


def format_verification_results(vr: VerificationResults) -> str:
    """Format verification results for inclusion in Reviewer evidence prompt."""
    if vr.error:
        return f"### Mechanical Verification (run by orchestrator — authoritative)\nERROR: {vr.error}\n"

    lines = [
        "### Mechanical Verification (run by orchestrator — authoritative)",
        f"Result: {vr.summary}",
    ]
    for s in vr.steps:
        tag = "PASS" if s.passed else "FAIL"
        detail = f"  [{tag}] {s.command}  (exit {s.exit_code})"
        if s.stdout.strip():
            detail += f"\n         stdout: {s.stdout.strip()[:200]}"
        if s.stderr.strip() and not s.passed:
            detail += f"\n         stderr: {s.stderr.strip()[:200]}"
        lines.append(detail)

    return "\n".join(lines)
