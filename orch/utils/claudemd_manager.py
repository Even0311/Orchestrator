"""Manages CLAUDE.md in the target project for Claude Code native context loading."""
from pathlib import Path

MARKER = "<!-- managed by orchestrator — do not edit this section manually -->"


def generate_claudemd(state_dir: Path, codebase_path: Path) -> None:
    """Generate or update CLAUDE.md in the target project from orchestrator state docs.

    Extracts stable project context (architecture, conventions, current phase) and
    writes it to CLAUDE.md so Claude Code loads it natively. This separates "what
    the project is" (CLAUDE.md) from "what to do this round" (executor prompt).

    If CLAUDE.md already exists with non-orchestrator content, the orchestrator
    section is appended/updated using markers.
    """
    orchestrator_section = _build_section(state_dir)
    claudemd_path = codebase_path / "CLAUDE.md"

    if claudemd_path.exists():
        existing = claudemd_path.read_text()
        if MARKER in existing:
            # Replace existing orchestrator section
            before, _ = existing.split(MARKER, 1)
            # Find the end marker if present
            end_marker = "<!-- end orchestrator section -->"
            if end_marker in existing:
                _, after = existing.rsplit(end_marker, 1)
            else:
                after = ""
            new_content = before.rstrip() + "\n\n" + orchestrator_section + after
        else:
            # Append orchestrator section to existing content
            new_content = existing.rstrip() + "\n\n" + orchestrator_section
    else:
        new_content = orchestrator_section

    claudemd_path.write_text(new_content.strip() + "\n")


def _build_section(state_dir: Path) -> str:
    """Build the orchestrator-managed section of CLAUDE.md."""
    parts = [MARKER, ""]

    # Architecture and conventions from designer context
    designer_ctx_path = state_dir / "context" / "designer.md"
    if designer_ctx_path.exists():
        designer_ctx = designer_ctx_path.read_text()
        architecture = _extract_section(designer_ctx, "Architecture Snapshot")
        constraints = _extract_section(designer_ctx, "Active Constraints")

        if architecture:
            parts.append("## Architecture")
            parts.append(architecture)
            parts.append("")
        if constraints:
            parts.append("## Conventions & Constraints")
            parts.append(constraints)
            parts.append("")

    # Current phase summary (goal only, not task queue)
    phase_path = state_dir / "current_phase.md"
    if phase_path.exists():
        phase_content = phase_path.read_text()
        phase_goal = _extract_section(phase_content, "Phase Goal")
        # Also grab the phase title from the first heading
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
    if designer_ctx_path.exists():
        assumptions = _extract_section(designer_ctx, "Working Assumptions")
        if assumptions:
            parts.append("## Working Assumptions")
            parts.append(assumptions)
            parts.append("")

    parts.append("<!-- end orchestrator section -->")
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
