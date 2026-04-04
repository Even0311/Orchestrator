"""Source-of-Truth (SOT) operations — parsing and updating project documents."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PhaseInfo:
    """Parsed phase information from current_phase.md."""
    phase_id: str          # e.g. "P28"
    phase_title: str       # e.g. "P28: Deterministic Relational Appraisal Expansion"
    phase_goal: str
    next_task_key: str     # e.g. "P28-T6" — first unfinished `- [ ]` entry, or "" if none
    next_task_desc: str    # description text after the task_key
    all_done: bool         # True if Task Queue has no `- [ ]` entries


def parse_current_phase(sot_dir: Path) -> PhaseInfo:
    """Parse current_phase.md from the SOT directory.

    Extracts the phase_id from the title heading and finds the first
    unchecked task in the Task Queue section.
    """
    phase_path = sot_dir / "current_phase.md"
    if not phase_path.exists():
        return PhaseInfo(
            phase_id="", phase_title="", phase_goal="",
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

    # Extract phase goal
    phase_goal = _extract_section(content, "Phase Goal")

    # Find first unfinished task in Task Queue
    queue_section = _extract_section(content, "Task Queue")
    next_task_key = ""
    next_task_desc = ""
    has_unchecked = False

    for line in queue_section.splitlines():
        line = line.strip()
        if line.startswith("- [ ]"):
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
        next_task_key=next_task_key,
        next_task_desc=next_task_desc,
        all_done=not has_unchecked,
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
