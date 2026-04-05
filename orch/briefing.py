"""Runtime briefing generation — orchestrator writes context for Claude to read."""
from __future__ import annotations

import json
import re
from pathlib import Path

from orch.models import TaskContract
from orch.sot import PhaseInfo, _split_h2_sections


def generate_round_brief(
    *,
    round_dir: Path,
    sot_dir: Path,
    phase_info: PhaseInfo,
    round_id: str,
    attempt_num: int,
    prior_failure: str = "",
    recent_rounds_summary: str = "",
) -> Path:
    """Generate round_brief.md in the round directory for Claude to read.

    This is the primary context handoff from orchestrator to Claude.
    Claude reads this via --add-dir pointing at the round directory.
    """
    round_dir.mkdir(parents=True, exist_ok=True)

    parts = [
        f"# Round Brief — {round_id} (attempt {attempt_num})",
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
        f"## Selected Task",
        f"**Task Key:** {phase_info.next_task_key}",
        f"**Description:** {phase_info.next_task_desc}",
        "",
    ])

    # ── Decisions Context ────────────────────────────────────────────────
    decisions_path = sot_dir / "decisions.md"
    if decisions_path.exists():
        decisions_text = decisions_path.read_text().strip()
        if decisions_text and len(decisions_text) > 50:
            recent = _extract_recent_decisions(decisions_text, count=3)
            if recent:
                parts.extend(["## Decisions Context (recent)", recent, ""])

    # ── Recent Rounds ────────────────────────────────────────────────────
    if recent_rounds_summary:
        parts.extend(["## Recent Rounds", recent_rounds_summary, ""])

    # ── Prior Failure ────────────────────────────────────────────────────
    if prior_failure:
        parts.extend([
            "## Prior Attempt Failed",
            "The previous attempt for this task failed. Fix the issues below:",
            prior_failure,
            "",
        ])

    # ── Instructions ─────────────────────────────────────────────────────
    parts.extend([
        "## Instructions",
        "1. The designer subagent should read this brief and produce a task_contract.json",
        "2. The executor subagent should implement the task",
        "3. The reviewer subagent should verify the implementation",
        "4. Write all artifact files to the round directory (accessible via --add-dir)",
        "",
        "## Artifact Files to Produce",
        "- `task_contract.json` — designer's task definition",
        "- `execution_evidence.json` — executor's self-report",
        "- `review_verdict.json` — reviewer's verdict",
        "",
    ])

    brief_path = round_dir / "round_brief.md"
    brief_path.write_text("\n".join(parts))
    return brief_path


def _extract_recent_decisions(decisions_text: str, count: int = 3) -> str:
    """Extract the last N H2 sections from decisions.md."""
    sections = _split_h2_sections(decisions_text)
    if not sections:
        return ""
    recent = sections[-count:]
    parts = []
    for heading, body in recent:
        parts.append(heading)
        parts.append(body.strip())
        parts.append("")
    return "\n".join(parts).strip()


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
    current_heading = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            # Check if this heading matches any section we want
            match = False
            for target in sections_to_include:
                if target.lower() in heading_text.lower():
                    match = True
                    break
            if match:
                capturing = True
                current_heading = stripped
                result_parts.append(current_heading)
            else:
                capturing = False
        elif capturing:
            # Skip HTML comments
            if stripped.startswith("<!--") and "-->" in stripped:
                continue
            result_parts.append(line)

    text = "\n".join(result_parts).strip()
    # Truncate if too long
    if len(text) > 1500:
        text = text[:1500] + "\n...(truncated)"
    return text


def _extract_roadmap_context(roadmap_text: str, current_phase_id: str) -> str:
    """Extract relevant roadmap context for the current phase.

    Finds the section containing the current phase_id (e.g. "P28") and
    returns it plus immediate neighbor sections. Does not dump the entire
    roadmap.
    """
    if not current_phase_id:
        # No phase_id to match — return first 800 chars as generic context
        truncated = roadmap_text[:800]
        if len(roadmap_text) > 800:
            truncated += "\n...(truncated)"
        return truncated

    # Split roadmap into H2 sections
    sections = _split_h2_sections(roadmap_text)

    if not sections:
        return roadmap_text[:800] if roadmap_text else ""

    # Find which section mentions the current phase_id
    target_idx = None
    for i, (heading, body) in enumerate(sections):
        if current_phase_id in heading or current_phase_id in body:
            target_idx = i
            break

    if target_idx is None:
        # Phase not found in roadmap — include the last substantive section
        # as nearest context
        for i in range(len(sections) - 1, -1, -1):
            if sections[i][1].strip():
                target_idx = i
                break

    if target_idx is None:
        return ""

    # Include target section and one neighbor on each side
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



def write_task_contract(round_dir: Path, contract: TaskContract) -> Path:
    """Write task_contract.json to round directory (orchestrator or designer writes this)."""
    path = round_dir / "task_contract.json"
    path.write_text(contract.to_json())
    return path


def read_artifacts(round_dir: Path) -> dict:
    """Read all artifact files from the round directory after Claude finishes.

    Returns a dict with keys: task_contract, execution_evidence, review_verdict.
    Each value is a parsed dict or None if the file doesn't exist.
    """
    artifacts = {}
    for name in ("task_contract", "execution_evidence", "review_verdict"):
        path = round_dir / f"{name}.json"
        if path.exists():
            try:
                artifacts[name] = json.loads(path.read_text())
            except json.JSONDecodeError:
                artifacts[name] = None
        else:
            artifacts[name] = None
    return artifacts
