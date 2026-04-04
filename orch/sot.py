"""Source-of-Truth (SOT) operations — parsing and updating project documents."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PhaseInfo:
    """Parsed phase information from current_phase.md."""
    phase_id: str          # e.g. "P28"
    phase_title: str       # e.g. "P28: Deterministic Relational Appraisal Expansion"
    phase_goal: str
    in_scope: str          # content of ## In Scope section, or ""
    out_of_scope: str      # content of ## Out of Scope section, or ""
    next_task_key: str     # e.g. "P28-T6" — first unfinished `- [ ]` entry, or "" if none
    next_task_desc: str    # description text after the task_key
    all_done: bool         # True if Task Queue has no `- [ ]` entries
    recent_completed: list[str] = field(default_factory=list)  # last N completed task descriptions from queue


def parse_current_phase(sot_dir: Path) -> PhaseInfo:
    """Parse current_phase.md from the SOT directory.

    Extracts the phase_id from the title heading and finds the first
    unchecked task in the Task Queue section.
    """
    phase_path = sot_dir / "current_phase.md"
    if not phase_path.exists():
        return PhaseInfo(
            phase_id="", phase_title="", phase_goal="",
            in_scope="", out_of_scope="",
            next_task_key="", next_task_desc="", all_done=True,
        )

    content = phase_path.read_text()
    return _parse_phase_content(content)


def _parse_phase_content(content: str) -> PhaseInfo:
    """Parse current_phase.md content into PhaseInfo."""
    # Extract title from first H1
    phase_title = ""
    phase_id = ""
    for line in content.splitlines():
        if line.startswith("# "):
            phase_title = line.lstrip("# ").strip()
            # Extract phase_id: look for P\d+ pattern
            m = re.search(r"(P\d+)", phase_title)
            if m:
                phase_id = m.group(1)
            break

    # Extract phase goal, scope
    phase_goal = _extract_section(content, "Phase Goal")
    in_scope = _extract_section(content, "In Scope")
    out_of_scope = _extract_section(content, "Out of Scope")

    # Find first unfinished task in Task Queue and collect completed items
    queue_section = _extract_section(content, "Task Queue")
    next_task_key = ""
    next_task_desc = ""
    has_unchecked = False
    completed_items: list[str] = []

    for line in queue_section.splitlines():
        line = line.strip()
        if line.startswith("- [x]"):
            completed_items.append(line[5:].strip())
        elif line.startswith("- [ ]"):
            has_unchecked = True
            if not next_task_key:
                # Parse "- [ ] P28-T6: description text"
                remainder = line[5:].strip()
                m = re.match(r"(P\d+-T\d+)\s*:\s*(.*)", remainder)
                if m:
                    next_task_key = m.group(1)
                    next_task_desc = m.group(2).strip()
                else:
                    # Fallback: use the whole remainder as desc
                    next_task_key = remainder.split(":")[0].strip() if ":" in remainder else remainder.split()[0] if remainder.split() else ""
                    next_task_desc = remainder

    return PhaseInfo(
        phase_id=phase_id,
        phase_title=phase_title,
        phase_goal=phase_goal,
        in_scope=in_scope,
        out_of_scope=out_of_scope,
        next_task_key=next_task_key,
        next_task_desc=next_task_desc,
        all_done=not has_unchecked,
        recent_completed=completed_items[-5:],
    )


def mark_task_complete(sot_dir: Path, task_key: str, completion_note: str = "") -> bool:
    """Mark a specific task_key as complete in current_phase.md.

    Converts `- [ ] TASK_KEY: desc` to `- [x] TASK_KEY: desc — completion_note`
    Returns True if the task was found and marked.
    """
    phase_path = sot_dir / "current_phase.md"
    if not phase_path.exists():
        return False

    content = phase_path.read_text()
    # Match the exact task_key in an unchecked line
    pattern = re.compile(
        r"^(- \[ \] " + re.escape(task_key) + r":\s*)(.*?)$",
        re.MULTILINE,
    )
    m = pattern.search(content)
    if not m:
        return False

    desc = m.group(2).strip()
    if completion_note:
        replacement = f"- [x] {task_key}: {desc} — {completion_note}"
    else:
        replacement = f"- [x] {task_key}: {desc}"

    new_content = content[:m.start()] + replacement + content[m.end():]
    phase_path.write_text(new_content)
    return True


def append_decision_entry(
    sot_dir: Path,
    *,
    round_id: str,
    phase_id: str,
    task_key: str,
    task_title: str,
    outcome_summary: str,
    hard_gate_summary: str = "",
    notes: str = "",
) -> bool:
    """Append a structured decision entry to decisions.md on successful round.

    Only called on PASS. Append-only — never modifies existing entries.
    Returns True if the entry was written.
    """
    from datetime import datetime, timezone
    decisions_path = sot_dir / "decisions.md"
    if not decisions_path.exists():
        return False

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    entry_parts = [
        f"## {ts} — {round_id}: {task_key}",
        f"**Phase:** {phase_id}",
        f"**Task:** {task_title}",
        f"**Outcome:** {outcome_summary}",
    ]
    if hard_gate_summary:
        entry_parts.append(f"**Hard gates:** {hard_gate_summary}")
    if notes:
        entry_parts.append(f"**Notes:** {notes}")

    entry = "\n".join(entry_parts)

    existing = decisions_path.read_text()
    decisions_path.write_text(existing.rstrip() + "\n\n" + entry + "\n")
    return True


def is_phase_complete(sot_dir: Path) -> bool:
    """Check if the current phase has no remaining unchecked tasks."""
    info = parse_current_phase(sot_dir)
    return info.all_done


def get_phase_status(sot_dir: Path) -> str:
    """Read phase status from current_phase.md HTML comment.

    Returns "draft", "approved", or "" (legacy files without status → treated as approved).
    """
    phase_path = sot_dir / "current_phase.md"
    if not phase_path.exists():
        return ""
    content = phase_path.read_text()
    m = re.search(r"<!--\s*status:\s*(\w+)\s*-->", content)
    return m.group(1) if m else ""


def set_phase_status(sot_dir: Path, status: str) -> bool:
    """Set or update the phase status comment in current_phase.md.

    Inserts after the H1 title line. Returns True if successful.
    """
    phase_path = sot_dir / "current_phase.md"
    if not phase_path.exists():
        return False
    content = phase_path.read_text()
    new_comment = f"<!-- status: {status} -->"

    # Replace existing status comment
    if re.search(r"<!--\s*status:\s*\w+\s*-->", content):
        content = re.sub(r"<!--\s*status:\s*\w+\s*-->", new_comment, content)
    else:
        # Insert after first H1 line
        lines = content.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.strip().startswith("# "):
                lines.insert(i + 1, new_comment + "\n")
                break
        content = "".join(lines)

    phase_path.write_text(content)
    return True


def extract_next_phase_from_roadmap(roadmap_text: str, current_phase_id: str) -> dict | None:
    """Find the phase section after current_phase_id in the roadmap.

    Returns dict with keys: phase_id, title, goal, in_scope, out_of_scope, full_section
    or None if not found.
    """
    sections = _split_h2_sections(roadmap_text)

    # Find current phase index — match "P28" against "Phase 28" or "P28" in heading
    # Extract the numeric part from current_phase_id (e.g. "P28" → "28")
    num_match = re.search(r"(\d+)", current_phase_id)
    phase_num = num_match.group(1) if num_match else current_phase_id

    current_idx = None
    for i, (heading, body) in enumerate(sections):
        if current_phase_id in heading or f"Phase {phase_num}" in heading:
            current_idx = i
            break

    if current_idx is None or current_idx + 1 >= len(sections):
        return None

    next_heading, next_body = sections[current_idx + 1]

    # Extract phase_id from heading (e.g. "## Phase 29 — ..." → "P29")
    m = re.search(r"Phase\s+(\d+)", next_heading)
    if not m:
        return None
    phase_id = f"P{m.group(1)}"

    # Clean title: "## Phase 29 — Appraisal..." → "P29: Appraisal..."
    title_part = re.sub(r"^##\s*Phase\s+\d+\w?\s*[—–-]\s*", "", next_heading).strip()
    title = f"{phase_id}: {title_part}"

    # Extract H3 subsections from body
    goal = _extract_h3_section(next_body, "Goal")
    in_scope = _extract_h3_section(next_body, "In Scope")
    out_of_scope = _extract_h3_section(next_body, "Out of Scope")

    return {
        "phase_id": phase_id,
        "title": title,
        "goal": goal,
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "full_section": next_heading + "\n" + next_body,
    }


def _split_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown text into (heading, body) pairs at ## boundaries."""
    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_body_lines: list[str] = []

    for line in text.splitlines():
        if line.strip().startswith("## "):
            if current_heading:
                sections.append((current_heading, "\n".join(current_body_lines)))
            current_heading = line.strip()
            current_body_lines = []
        else:
            current_body_lines.append(line)

    if current_heading:
        sections.append((current_heading, "\n".join(current_body_lines)))

    return sections


def _extract_h3_section(body: str, heading: str) -> str:
    """Extract content under a ### heading until the next ### or end."""
    lines = body.splitlines()
    capturing = False
    result = []

    for line in lines:
        if line.strip().startswith("### ") and heading.lower() in line.lower():
            capturing = True
            continue
        elif capturing and line.strip().startswith("### "):
            break
        elif capturing:
            result.append(line)

    return "\n".join(result).strip()


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

    return "\n".join(result).strip()
