"""Runtime briefing generation — orchestrator writes role-specific context for each Claude session.

Each agent (designer, executor, evaluator) gets a different brief with only the
context it needs. This ensures context isolation between agents.
"""
from __future__ import annotations

import json
from pathlib import Path

from orch.models import TaskContract
from orch.sot import PhaseInfo, _split_h2_sections


# ── Designer Brief ──────────────────────────────────────────────────────────

def generate_designer_brief(
    *,
    round_dir: Path,
    sot_dir: Path,
    phase_info: PhaseInfo,
    round_id: str,
    prior_failure: str = "",
    recent_rounds_summary: str = "",
) -> Path:
    """Generate designer_brief.md — vision, roadmap, phase context, prior issues.

    Designer sees the full project context to make informed planning decisions,
    but never sees executor code or evaluator reasoning.
    """
    round_dir.mkdir(parents=True, exist_ok=True)

    parts = [
        f"# Designer Brief — {round_id}",
        "",
    ]

    # ── Project Vision Context ───────────────────────────────────────────
    vision_path = sot_dir / "vision.md"
    if vision_path.exists():
        vision_text = vision_path.read_text().strip()
        vision_summary = _extract_vision_summary(vision_text)
        if vision_summary:
            parts.extend(["## Project Vision Context", vision_summary, ""])

    # ── Roadmap / Phase Context ──────────────────────────────────────────
    roadmap_path = sot_dir / "road_map.md"
    if roadmap_path.exists():
        roadmap_text = roadmap_path.read_text().strip()
        roadmap_context = _extract_roadmap_context(roadmap_text, phase_info.phase_id)
        if roadmap_context:
            parts.extend(["## Roadmap / Phase Context", roadmap_context, ""])

    # ── Current Phase Context ────────────────────────────────────────────
    parts.extend([
        f"## Current Phase: {phase_info.phase_title}",
        f"**Phase ID:** {phase_info.phase_id}",
        f"**Phase Goal:** {phase_info.phase_goal}",
        "",
    ])
    if phase_info.in_scope:
        parts.extend(["**In Scope:**", phase_info.in_scope, ""])
    if phase_info.out_of_scope:
        parts.extend(["**Out of Scope:**", phase_info.out_of_scope, ""])

    # ── Recently Completed Tasks ────────────────────────────────────────
    if phase_info.recent_completed:
        parts.append("## Recently Completed Tasks (same phase)")
        for item in phase_info.recent_completed:
            parts.append(f"- {item}")
        parts.append("")

    # ── Selected Task ────────────────────────────────────────────────────
    parts.extend([
        "## Selected Task",
        f"**Task Key:** {phase_info.next_task_key}",
        f"**Description:** {phase_info.next_task_desc}",
        "",
    ])

    # ── Recent Rounds ────────────────────────────────────────────────────
    if recent_rounds_summary:
        parts.extend(["## Recent Rounds", recent_rounds_summary, ""])

    # ── Prior Failure ────────────────────────────────────────────────────
    if prior_failure:
        parts.extend([
            "## Prior Round Failed — Issues to Address",
            "The previous round for this task failed. Your new contract must address these issues:",
            prior_failure,
            "",
        ])

    # ── Output Instructions ──────────────────────────────────────────────
    parts.extend([
        "## Your Task",
        "Produce a `task_contract.json` file with the following fields:",
        "- `phase_id`, `task_key`, `title`, `objective`, `exact_scope`",
        "- `constraints` — architectural constraints the executor must respect",
        "- `forbidden_files` — glob patterns for files the executor must NOT touch",
        "- `non_goals` — what is explicitly out of scope",
        "- `acceptance_criteria` — each criterion must be objectively verifiable",
        "- `review_focus` — what the evaluator should pay special attention to",
        "",
        "Write the contract to tell the executor WHAT to do and WHAT NOT to touch,",
        "not HOW to implement it. The executor decides implementation details.",
        "",
    ])

    brief_path = round_dir / "designer_brief.md"
    brief_path.write_text("\n".join(parts))
    return brief_path


# ── Executor Brief ──────────────────────────────────────────────────────────

def generate_executor_brief(
    *,
    round_dir: Path,
    task_contract: TaskContract,
    round_id: str,
    is_retry: bool = False,
) -> Path:
    """Generate executor_brief.md — task contract only.

    Executor sees the finalized contract and has access to source code.
    It never sees designer reasoning, vision docs, or evaluator feedback.
    """
    round_dir.mkdir(parents=True, exist_ok=True)

    parts = [
        f"# Executor Brief — {round_id}",
        "",
        "## Task Contract",
        f"**Task Key:** {task_contract.task_key}",
        f"**Title:** {task_contract.title}",
        f"**Objective:** {task_contract.objective}",
        "",
    ]

    if task_contract.exact_scope:
        parts.append("**Exact Scope:**")
        scope = task_contract.exact_scope
        if isinstance(scope, list):
            for item in scope:
                parts.append(f"- {item}")
        else:
            parts.append(scope)
        parts.append("")

    if task_contract.constraints:
        parts.append("**Constraints:**")
        for c in task_contract.constraints:
            parts.append(f"- {c}")
        parts.append("")

    if task_contract.forbidden_files:
        parts.append("**Forbidden Files (DO NOT modify):**")
        for f in task_contract.forbidden_files:
            parts.append(f"- `{f}`")
        parts.append("")

    if task_contract.non_goals:
        parts.append("**Non-Goals (DO NOT do):**")
        for ng in task_contract.non_goals:
            parts.append(f"- {ng}")
        parts.append("")

    if task_contract.acceptance_criteria:
        parts.append("**Acceptance Criteria:**")
        for ac in task_contract.acceptance_criteria:
            parts.append(f"- {ac}")
        parts.append("")

    parts.extend([
        "## Your Task",
        "1. Read the codebase and understand the relevant code",
        "2. Implement the changes described in the contract",
        "3. Write/update tests as needed",
        "4. Run the test suite to verify no regressions",
        "5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues",
        "",
    ])

    if is_retry:
        parts.extend([
            "## Important: This is a retry",
            "A previous attempt at this task failed review. After applying the required fixes,",
            "do NOT stop — review your entire output for the same class of error in other locations.",
            "A fix in one place often means the same mistake exists elsewhere.",
            "",
        ])

    brief_path = round_dir / "executor_brief.md"
    brief_path.write_text("\n".join(parts))
    return brief_path


# ── Evaluator Contract Brief ────────────────────────────────────────────────

def generate_evaluator_contract_brief(
    *,
    round_dir: Path,
    task_contract: TaskContract,
    round_id: str,
) -> Path:
    """Generate evaluator_contract_brief.md — acceptance criteria and review focus only.

    Evaluator reviews whether the proposed criteria are objectively verifiable.
    It does NOT see vision, roadmap, or designer reasoning.
    """
    round_dir.mkdir(parents=True, exist_ok=True)

    parts = [
        f"# Evaluator Contract Review — {round_id}",
        "",
        f"**Task Key:** {task_contract.task_key}",
        f"**Title:** {task_contract.title}",
        "",
    ]

    if task_contract.acceptance_criteria:
        parts.append("## Proposed Acceptance Criteria")
        for i, ac in enumerate(task_contract.acceptance_criteria, 1):
            parts.append(f"{i}. {ac}")
        parts.append("")

    if task_contract.review_focus:
        parts.append("## Proposed Review Focus")
        for rf in task_contract.review_focus:
            parts.append(f"- {rf}")
        parts.append("")

    parts.extend([
        "## Your Task",
        "Review the proposed acceptance criteria and review focus above.",
        "For each criterion, determine whether you can objectively verify it after code is written.",
        "",
        "Write `contract_feedback.json` with:",
        "- `can_evaluate` — list of criteria you can objectively verify",
        "- `cannot_evaluate` — list of criteria that are too vague or subjective to verify",
        "- `suggested_changes` — concrete rewrites for vague criteria",
        "- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable",
        "",
    ])

    brief_path = round_dir / "evaluator_contract_brief.md"
    brief_path.write_text("\n".join(parts))
    return brief_path


# ── Evaluator Review Brief ──────────────────────────────────────────────────

def generate_evaluator_review_brief(
    *,
    round_dir: Path,
    task_contract: TaskContract,
    git_diff: str,
    round_id: str,
) -> Path:
    """Generate evaluator_review_brief.md — git diff + acceptance criteria + review focus.

    Evaluator checks actual code changes against the contract criteria.
    It does NOT see executor reasoning, designer reasoning, or vision docs.
    """
    round_dir.mkdir(parents=True, exist_ok=True)

    parts = [
        f"# Evaluator Code Review — {round_id}",
        "",
        f"**Task Key:** {task_contract.task_key}",
        f"**Title:** {task_contract.title}",
        "",
    ]

    if task_contract.acceptance_criteria:
        parts.append("## Acceptance Criteria")
        for i, ac in enumerate(task_contract.acceptance_criteria, 1):
            parts.append(f"{i}. {ac}")
        parts.append("")

    if task_contract.review_focus:
        parts.append("## Review Focus")
        for rf in task_contract.review_focus:
            parts.append(f"- {rf}")
        parts.append("")

    parts.extend([
        "## Code Changes (git diff)",
        "```diff",
        git_diff if git_diff else "(no diff available)",
        "```",
        "",
        "## Your Task",
        "1. Check each acceptance criterion against the actual code changes",
        "2. Pay special attention to the review focus items",
        "3. If existing test files were modified, examine whether the modifications are justified",
        "4. Verify tests pass and no regressions were introduced",
        "",
        "Write `review_verdict.json` with:",
        "- `verdict` — PASS, FAIL, or REVISION_REQUIRED",
        "- `confidence` — high, medium, or low",
        "- `met_criteria` — list of criteria that passed",
        "- `unmet_criteria` — list of criteria that failed",
        "- `blocker_fixes` — must-fix issues (empty if PASS)",
        "- `non_blocking_suggestions` — nice-to-have improvements",
        "- `rationale` — explanation of verdict",
        "",
    ])

    brief_path = round_dir / "evaluator_review_brief.md"
    brief_path.write_text("\n".join(parts))
    return brief_path


# ── Shared Helpers ──────────────────────────────────────────────────────────


def _extract_vision_summary(vision_text: str) -> str:
    """Extract concise, stable constraints from vision.md.

    Pulls: Project Goal, Core Features, Tech Stack, Out of Scope.
    Skips: codebase path, current status details.
    """
    sections_to_include = [
        "Project Goal",
        "Core Features",
        "Tech Stack",
        "Out of Scope",
        # Chinese variants
        "项目目标",
        "核心功能",
        "技术栈",
        "不做什么",
    ]

    lines = vision_text.splitlines()
    result_parts = []
    capturing = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            match = False
            for target in sections_to_include:
                if target.lower() in heading_text.lower():
                    match = True
                    break
            if match:
                capturing = True
                result_parts.append(stripped)
            else:
                capturing = False
        elif capturing:
            if stripped.startswith("<!--") and "-->" in stripped:
                continue
            result_parts.append(line)

    text = "\n".join(result_parts).strip()
    if len(text) > 1500:
        text = text[:1500] + "\n...(truncated)"
    return text


def _extract_roadmap_context(roadmap_text: str, current_phase_id: str) -> str:
    """Extract relevant roadmap context for the current phase."""
    if not current_phase_id:
        truncated = roadmap_text[:800]
        if len(roadmap_text) > 800:
            truncated += "\n...(truncated)"
        return truncated

    sections = _split_h2_sections(roadmap_text)

    if not sections:
        return roadmap_text[:800] if roadmap_text else ""

    target_idx = None
    for i, (heading, body) in enumerate(sections):
        if current_phase_id in heading or current_phase_id in body:
            target_idx = i
            break

    if target_idx is None:
        for i in range(len(sections) - 1, -1, -1):
            if sections[i][1].strip():
                target_idx = i
                break

    if target_idx is None:
        return ""

    start = max(0, target_idx - 1)
    end = min(len(sections), target_idx + 2)
    context_parts = []
    for heading, body in sections[start:end]:
        context_parts.append(heading)
        context_parts.append(body.strip())
        context_parts.append("")

    text = "\n".join(context_parts).strip()
    if len(text) > 2000:
        text = text[:2000] + "\n...(truncated)"
    return text


# ── Artifact I/O ────────────────────────────────────────────────────────────

def write_task_contract(round_dir: Path, contract: TaskContract) -> Path:
    """Write task_contract.json to round directory."""
    path = round_dir / "task_contract.json"
    path.write_text(contract.to_json())
    return path


def read_artifacts(round_dir: Path) -> dict:
    """Read all artifact files from the round directory after Claude finishes.

    Returns a dict with keys: task_contract, execution_evidence, review_verdict,
    contract_feedback. Each value is a parsed dict or None if the file doesn't exist.
    """
    artifacts = {}
    for name in ("task_contract", "execution_evidence", "review_verdict", "contract_feedback"):
        path = round_dir / f"{name}.json"
        if path.exists():
            try:
                artifacts[name] = json.loads(path.read_text())
            except json.JSONDecodeError:
                artifacts[name] = None
        else:
            artifacts[name] = None
    return artifacts
