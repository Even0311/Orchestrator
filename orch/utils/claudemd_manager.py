"""Manages the dynamic section of CLAUDE.md in the target project.

CLAUDE.md has two parts:
- Stable sections (project def, tech stack, architecture, hard rules, etc.)
  Written once by human or initial generation. Rarely changes.
- Dynamic section (current phase goal, working assumptions)
  Updated by orchestrator each round via markers.

This module only updates the dynamic section. The stable sections are preserved.
"""
from pathlib import Path

DYNAMIC_START = "<!-- managed by orchestrator — stable sections above, dynamic sections below -->"
DYNAMIC_END = "<!-- end orchestrator dynamic section -->"


def generate_claudemd(state_dir: Path, codebase_path: Path) -> None:
    """Update only the dynamic section of CLAUDE.md in the target project.

    If CLAUDE.md doesn't exist or has no dynamic markers, the dynamic section
    is appended. If markers exist, the content between them is replaced.

    Performs a diff check: skips the write if content hasn't changed.
    """
    dynamic_section = _build_dynamic_section(state_dir)
    claudemd_path = codebase_path / "CLAUDE.md"

    if claudemd_path.exists():
        existing = claudemd_path.read_text()

        if DYNAMIC_START in existing:
            # Replace dynamic section between markers
            before = existing.split(DYNAMIC_START, 1)[0].rstrip()
            after = ""
            if DYNAMIC_END in existing:
                after = existing.rsplit(DYNAMIC_END, 1)[1]

            new_content = before + "\n\n" + dynamic_section + after
        else:
            # No markers yet — append dynamic section
            new_content = existing.rstrip() + "\n\n" + dynamic_section

        new_content = new_content.strip() + "\n"

        # Diff check: skip write if unchanged
        if new_content == existing:
            return

        claudemd_path.write_text(new_content)
    else:
        # No CLAUDE.md at all — write just the dynamic section
        # (stable sections should be generated separately)
        claudemd_path.write_text(dynamic_section.strip() + "\n")


def _build_dynamic_section(state_dir: Path) -> str:
    """Build the orchestrator-managed dynamic section of CLAUDE.md."""
    parts = [DYNAMIC_START, ""]

    # Current phase summary (goal only, not full task queue)
    phase_path = state_dir / "current_phase.md"
    if phase_path.exists():
        phase_content = phase_path.read_text()
        phase_goal = _extract_section(phase_content, "Phase Goal")
        phase_title = ""
        for line in phase_content.splitlines():
            if line.startswith("# "):
                phase_title = line.lstrip("# ").strip()
                break

        if phase_title or phase_goal:
            parts.append("## Current Phase")
            if phase_title:
                parts.append(phase_title)
            if phase_goal:
                parts.append(phase_goal)
            parts.append("")

    # Working assumptions from designer context
    designer_ctx_path = state_dir / "context" / "designer.md"
    if designer_ctx_path.exists():
        designer_ctx = designer_ctx_path.read_text()
        assumptions = _extract_section(designer_ctx, "Working Assumptions")
        if assumptions:
            parts.append("## Working Assumptions")
            parts.append(assumptions)
            parts.append("")

    # Next phase pointer from roadmap (if current phase is closing)
    roadmap_path = state_dir / "road_map.md"
    if roadmap_path.exists() and phase_path.exists():
        phase_content = phase_path.read_text().lower()
        if "phase complete" in phase_content or "all tasks done" in phase_content:
            parts.append("## Next Phase")
            parts.append("Current phase is complete. See orchestrator roadmap for next phase.")
            parts.append("")

    parts.append(DYNAMIC_END)
    return "\n".join(parts)


def _extract_section(content: str, heading: str) -> str:
    """Extract content under a ## heading until the next ## or end of file."""
    lines = content.splitlines()
    capturing = False
    result = []

    for line in lines:
        if line.strip().startswith("## ") and heading.lower() in line.lower():
            capturing = True
            continue
        elif capturing and line.strip().startswith("## "):
            break
        elif capturing:
            result.append(line)

    text = "\n".join(result).strip()
    return text if text else ""
