"""Phase planning — invoke Claude to generate task breakdown for a new phase."""
from __future__ import annotations

import json
import re
import subprocess

import click


def generate_task_breakdown(
    *,
    next_phase: dict,
    completed_phase_md: str,
    decisions_md: str,
    vision_md: str,
    model: str = "opus",
) -> list[str]:
    """Call Claude to generate task queue for next phase.

    Returns list of task lines like "- [ ] P29-T1: description".
    Raises RuntimeError if Claude invocation fails.
    """
    prompt = _build_planning_prompt(
        next_phase=next_phase,
        completed_phase_md=completed_phase_md,
        decisions_md=decisions_md,
        vision_md=vision_md,
    )

    click.echo(f"  Invoking Claude ({model}) for task breakdown...")
    result = _invoke_claude(prompt=prompt, model=model)

    if not result["success"]:
        raise RuntimeError(f"Claude invocation failed: {result['output']}")

    return _parse_task_lines(result["output"], next_phase["phase_id"])


def _build_planning_prompt(
    *,
    next_phase: dict,
    completed_phase_md: str,
    decisions_md: str,
    vision_md: str,
) -> str:
    """Build the prompt for task breakdown generation."""
    phase_id = next_phase["phase_id"]

    # Truncate long inputs
    if len(vision_md) > 2000:
        vision_md = vision_md[:2000] + "\n...(truncated)"
    if len(decisions_md) > 3000:
        decisions_md = "...(truncated)\n" + decisions_md[-3000:]
    if len(completed_phase_md) > 2000:
        completed_phase_md = completed_phase_md[:2000] + "\n...(truncated)"

    return (
        f"You are a project designer. Break down the next development phase into concrete, "
        f"ordered tasks.\n\n"
        f"## Project Vision\n{vision_md}\n\n"
        f"## Just-Completed Phase\n{completed_phase_md}\n\n"
        f"## Next Phase: {next_phase['title']}\n"
        f"**Goal:** {next_phase['goal']}\n\n"
        f"**In Scope:**\n{next_phase['in_scope']}\n\n"
        f"**Out of Scope:**\n{next_phase['out_of_scope']}\n\n"
        f"## Recent Decisions\n{decisions_md}\n\n"
        f"## Output Format\n"
        f"Return ONLY a task queue as a markdown checklist. Each line must follow this exact format:\n"
        f"- [ ] {phase_id}-T{{n}}: {{concise task description}}\n\n"
        f"Rules:\n"
        f"- Order tasks by logical dependency (earlier tasks enable later ones)\n"
        f"- Aim for 3-6 tasks per phase — prefer fewer, larger tasks over many small ones\n"
        f"- Group related work into a single task: e.g. a feature implementation + its tests + its docs = one task, not three\n"
        f"- Only split tasks when there is a true sequential dependency (task B needs task A's output to start)\n"
        f"- Tasks define WHAT, not HOW — no file paths or implementation details\n"
        f"- Do not include any text besides the task list\n"
    )


def _invoke_claude(*, prompt: str, model: str) -> dict:
    """Invoke Claude CLI for planning (no agent, no codebase access)."""
    cmd = [
        "claude",
        "-p", prompt,
        "--model", model,
        "--output-format", "json",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Claude timed out after 300s"}

    if proc.returncode != 0:
        return {"success": False, "output": proc.stderr or proc.stdout}

    # Parse JSON output from Claude
    try:
        data = json.loads(proc.stdout)
        text = data.get("result", "") or data.get("content", "") or proc.stdout
    except json.JSONDecodeError:
        text = proc.stdout

    return {"success": True, "output": text}


def _parse_task_lines(output: str, phase_id: str) -> list[str]:
    """Extract task queue lines from Claude output."""
    lines = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]") and phase_id in stripped:
            lines.append(stripped)

    if not lines:
        # Fallback: try to find any checkbox lines
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("- [ ]"):
                lines.append(stripped)

    return lines
