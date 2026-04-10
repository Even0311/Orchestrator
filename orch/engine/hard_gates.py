"""Post-Claude hard gates — programmatic, unbypassable verification.

These run after Claude finishes and before the orchestrator adjudicates.
Any failure here overrides Claude's internal reviewer verdict.
"""
from __future__ import annotations

import fnmatch
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from orch.models import ReviewVerdict, Verdict
from orch.utils.evidence_collector import GitEvidence


# ── Protected path rules ─────────────────────────────────────────────────────

# Target-repo files Claude must never modify (full relative paths or glob patterns).
TARGET_REPO_PROTECTED = (
    "CLAUDE.md",
    ".claude/agents/**",
)

# Orchestrator-side round directory: only these basenames are allowed as
# Claude-written artifacts inside the attempt directory.
ALLOWED_ROUND_ARTIFACTS = frozenset({
    "task_contract.json",
    "execution_evidence.json",
    "review_verdict.json",
    "contract_feedback.json",
})

# Files written by the orchestrator (not Claude) — allowed in round_dir
ORCHESTRATOR_WRITTEN_FILES = frozenset({
    "round_brief.md",           # legacy
    "designer_brief.md",
    "executor_brief.md",
    "evaluator_contract_brief.md",
    "evaluator_review_brief.md",
    "attempt_report.json",
})

# Canonical SOT files under projects/<name>/ that Claude must never mutate directly.
# Orchestrator-owned: only updated programmatically after final PASS adjudication.
CANONICAL_SOT_FILES = (
    "vision.md",
    "road_map.md",
    "current_phase.md",
    "decisions.md",
)


@dataclass
class GateResult:
    """Result of a single hard gate check."""
    name: str
    passed: bool
    detail: str = ""


@dataclass
class HardGateResults:
    """Aggregate result of all hard gate checks."""
    gates: list[GateResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(g.passed for g in self.gates)

    @property
    def failures(self) -> list[GateResult]:
        return [g for g in self.gates if not g.passed]

    def to_verdict(self) -> ReviewVerdict | None:
        """If any gate failed, return a FAIL verdict. Otherwise None."""
        if self.all_passed:
            return None
        reasons = [f"{g.name}: {g.detail}" for g in self.failures]
        return ReviewVerdict(
            verdict=Verdict.FAIL,
            confidence="high",
            unmet_criteria=reasons,
            blocker_fixes=reasons,
            rationale="Hard gate failure: " + "; ".join(reasons),
        )


def run_hard_gates(
    *,
    codebase_path: Path,
    git_evidence: GitEvidence,
    round_dir: Path | None = None,
    forbidden_files: list[str] | None = None,
    test_cmd: str | None = None,
) -> HardGateResults:
    """Run all hard gates and return aggregate results.

    Gates run after executor completes, before evaluator reviews.
    Any failure here skips the evaluator and directly fails the round.
    """
    results = HardGateResults()

    # Gate 1: Git diff — must have changes
    results.gates.append(_gate_has_changes(git_evidence))

    # Gate 2: Target-repo control-plane files (CLAUDE.md, .claude/agents/**)
    results.gates.append(_gate_target_protected_files(git_evidence))

    # Gate 3: Forbidden files (if specified)
    if forbidden_files:
        results.gates.append(_gate_forbidden_files(git_evidence, forbidden_files))

    # Gate 4: Round-dir artifact boundary (orchestrator-side SOT protection)
    if round_dir:
        results.gates.append(_gate_round_dir_boundary(round_dir))

    # Gate 5: Pytest
    results.gates.append(_gate_pytest(codebase_path, test_cmd))

    return results


# ── Gate implementations ─────────────────────────────────────────────────────

def _gate_has_changes(git_evidence: GitEvidence) -> GateResult:
    """Verify Claude actually made changes."""
    if git_evidence.has_changes:
        return GateResult(name="git_changes", passed=True)
    return GateResult(
        name="git_changes", passed=False,
        detail="No git changes detected — Claude may not have made any modifications",
    )


def _gate_target_protected_files(git_evidence: GitEvidence) -> GateResult:
    """Verify Claude did not modify protected control-plane files in the target repo.

    Protected: CLAUDE.md, .claude/agents/**
    """
    all_changed = git_evidence.files_modified + git_evidence.files_added + git_evidence.files_deleted
    violations = []
    for f in all_changed:
        if _matches_any_protected_pattern(f, TARGET_REPO_PROTECTED):
            violations.append(f)
    if violations:
        return GateResult(
            name="target_protected_files", passed=False,
            detail=f"Protected control-plane files modified: {', '.join(violations)}",
        )
    return GateResult(name="target_protected_files", passed=True)


def _matches_any_protected_pattern(filepath: str, patterns: tuple[str, ...]) -> bool:
    """Check if a filepath matches any protected pattern.

    Supports exact matches and glob patterns (e.g. '.claude/agents/**').
    """
    for pat in patterns:
        if fnmatch.fnmatch(filepath, pat):
            return True
        # Also check if the filepath is exactly the pattern (non-glob)
        if filepath == pat:
            return True
    return False


def _gate_round_dir_boundary(round_dir: Path) -> GateResult:
    """Verify Claude only wrote allowed artifact files to the round directory.

    Detects path traversal: any file written outside the exact round_dir,
    or any file inside round_dir that isn't an allowed artifact basename.

    This protects orchestrator-side canonical SOT from mutation via --add-dir.
    """
    if not round_dir.exists():
        return GateResult(name="round_dir_boundary", passed=True)

    resolved_round_dir = round_dir.resolve()
    violations = []

    for item in round_dir.rglob("*"):
        if item.is_dir():
            continue
        resolved = item.resolve()

        # Check path traversal: file must be directly in round_dir, not a child dir
        # (symlink escape, ../../ in name, etc.)
        if resolved.parent != resolved_round_dir:
            violations.append(f"file outside round dir: {item.name}")
            continue

        # Skip orchestrator-written files (briefs, reports)
        if item.name in ORCHESTRATOR_WRITTEN_FILES:
            continue

        # Check it's an allowed Claude-written artifact
        if item.name not in ALLOWED_ROUND_ARTIFACTS:
            violations.append(f"unexpected file in round dir: {item.name}")

    if violations:
        return GateResult(
            name="round_dir_boundary", passed=False,
            detail=f"Round directory boundary violated: {'; '.join(violations[:5])}",
        )
    return GateResult(name="round_dir_boundary", passed=True)



def _gate_forbidden_files(git_evidence: GitEvidence, forbidden_patterns: list[str]) -> GateResult:
    """Verify no changed files match any forbidden pattern."""
    all_changed = git_evidence.files_modified + git_evidence.files_added + git_evidence.files_deleted
    violations = []
    for f in all_changed:
        if any(fnmatch.fnmatch(f, pat) for pat in forbidden_patterns):
            violations.append(f)
    if violations:
        return GateResult(
            name="forbidden_files", passed=False,
            detail=f"Forbidden files modified: {', '.join(violations[:5])}",
        )
    return GateResult(name="forbidden_files", passed=True)


def _gate_pytest(codebase_path: Path, test_cmd: str | None = None, timeout: int = 120) -> GateResult:
    """Run pytest as a hard gate."""
    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")

    try:
        if test_cmd:
            proc = subprocess.run(
                test_cmd,
                shell=True,
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
        else:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                cwd=str(codebase_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
        output = proc.stdout + proc.stderr
        if proc.returncode == 0:
            return GateResult(name="pytest", passed=True)
        return GateResult(
            name="pytest", passed=False,
            detail=output[-500:] if output else "pytest exited with non-zero status",
        )
    except subprocess.TimeoutExpired:
        return GateResult(name="pytest", passed=False, detail=f"pytest timed out after {timeout}s")
    except FileNotFoundError:
        return GateResult(name="pytest", passed=False, detail="python not found in PATH")


# ── Canonical SOT mutation detection ─────────────────────────────────────────


def snapshot_sot_dir(sot_dir: Path, allowed_write_prefix: Path | None = None) -> dict[str, str]:
    """Snapshot all files under sot_dir, excluding the allowed write area.

    Returns {relative_path: sha256_hex} for every regular file outside
    the allowed_write_prefix subtree.  Called BEFORE Claude invocation.
    """
    if not sot_dir.exists():
        return {}

    resolved_sot = sot_dir.resolve()
    resolved_allowed = allowed_write_prefix.resolve() if allowed_write_prefix else None
    snapshot: dict[str, str] = {}

    for item in sot_dir.rglob("*"):
        if item.is_dir():
            continue
        resolved = item.resolve()
        if resolved_allowed and _is_under(resolved, resolved_allowed):
            continue
        rel = str(item.relative_to(sot_dir))
        snapshot[rel] = _file_hash(item)

    return snapshot


def detect_sot_mutation(
    before: dict[str, str],
    sot_dir: Path,
    allowed_write_prefix: Path | None = None,
) -> GateResult:
    """Compare before-snapshot with current filesystem state.

    Detects:
    - modifications to any canonical SOT file
    - deletions of any snapshotted file
    - new files created outside the allowed write area

    Called AFTER Claude invocation, before adjudication.
    """
    if not sot_dir.exists():
        return GateResult(name="sot_mutation", passed=True)

    resolved_allowed = allowed_write_prefix.resolve() if allowed_write_prefix else None
    violations: list[str] = []

    # Build current state (excluding allowed write area)
    current: dict[str, str] = {}
    for item in sot_dir.rglob("*"):
        if item.is_dir():
            continue
        resolved = item.resolve()
        if resolved_allowed and _is_under(resolved, resolved_allowed):
            continue
        rel = str(item.relative_to(sot_dir))
        current[rel] = _file_hash(item)

    # Detect modifications and deletions
    for rel, old_hash in before.items():
        new_hash = current.get(rel)
        if new_hash is None:
            violations.append(f"canonical SOT file deleted: {rel}")
        elif new_hash != old_hash:
            violations.append(f"canonical SOT file mutated: {rel}")

    # Detect new files created outside allowed write area
    for rel in current:
        if rel not in before:
            violations.append(f"unexpected file created in SOT area: {rel}")

    if violations:
        return GateResult(
            name="sot_mutation",
            passed=False,
            detail=f"Canonical SOT mutation detected: {'; '.join(violations[:10])}",
        )
    return GateResult(name="sot_mutation", passed=True)


def _file_hash(path: Path) -> str:
    """SHA-256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_under(child: Path, parent: Path) -> bool:
    """Check if resolved child path is under resolved parent path."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


# ── Scope policy: validate forbidden_files ─────────────────────────────────

# Patterns that must never appear in allowed scope (they'd cover control-plane)
CONTROL_PLANE_OVERLAP_PATTERNS = (
    "CLAUDE.md",
    ".claude/**",
    ".claude/agents/**",
    ".claude/agents/*",
)


@dataclass
class ScopeValidationResult:
    """Result of validating Claude-proposed file scope."""
    valid: bool
    sanitized_allowed: list[str]
    sanitized_forbidden: list[str]
    violations: list[str] = field(default_factory=list)


def validate_proposed_scope(
    proposed_forbidden: list[str],
) -> ScopeValidationResult:
    """Validate and normalize designer-proposed forbidden_files.

    Ensures control-plane files are always in the forbidden list.
    allowed_files is no longer used — executor is free to modify any file
    not in forbidden_files, with hard gates protecting SOT and control-plane.
    """
    violations = []
    sanitized_forbidden = list(proposed_forbidden)

    # Always ensure control-plane is in forbidden
    for cpat in CONTROL_PLANE_OVERLAP_PATTERNS:
        if cpat not in sanitized_forbidden:
            sanitized_forbidden.append(cpat)

    return ScopeValidationResult(
        valid=len(violations) == 0,
        sanitized_allowed=[],
        sanitized_forbidden=sanitized_forbidden,
        violations=violations,
    )


def _pattern_overlaps_control_plane(pattern: str) -> bool:
    """Check if a proposed pattern would match control-plane files."""
    # Test representative control-plane paths against the pattern
    control_plane_test_paths = [
        "CLAUDE.md",
        ".claude/agents/designer.md",
        ".claude/agents/executor.md",
        ".claude/agents/reviewer.md",
        ".claude/agents/round-driver.md",
    ]
    for test_path in control_plane_test_paths:
        if fnmatch.fnmatch(test_path, pattern):
            return True
    return False
