"""CLI commands for phase lifecycle management."""
from __future__ import annotations

import click

from orch.config.settings import load_config, PROJECTS_DIR
from orch.db.database import get_connection, get_active_project, now_iso
from orch.sot import (
    parse_current_phase,
    get_phase_status,
    set_phase_status,
    extract_next_phase_from_roadmap,
)
from orch.engine.phase_planner import generate_task_breakdown


@click.group("phase")
def phase_group():
    """Phase lifecycle management."""


@phase_group.command("next")
def phase_next_cmd():
    """Generate next phase's current_phase.md from roadmap + Claude designer."""
    project = get_active_project()
    if not project:
        click.echo("No active project. Run 'orch switch <name>' first.", err=True)
        raise SystemExit(1)

    project_name = project["name"]
    sot_dir = PROJECTS_DIR / project_name

    # Check current phase is complete
    phase_info = parse_current_phase(sot_dir)
    if not phase_info.all_done:
        click.echo(
            f"Current phase {phase_info.phase_id} still has unchecked tasks. "
            f"Complete all tasks before generating the next phase.",
            err=True,
        )
        raise SystemExit(1)

    current_phase_id = phase_info.phase_id
    if not current_phase_id:
        click.echo("Cannot determine current phase_id from current_phase.md.", err=True)
        raise SystemExit(1)

    # Read roadmap
    roadmap_path = sot_dir / "road_map.md"
    if not roadmap_path.exists():
        click.echo("road_map.md not found in SOT directory.", err=True)
        raise SystemExit(1)
    roadmap_text = roadmap_path.read_text()

    # Find next phase in roadmap
    next_phase = extract_next_phase_from_roadmap(roadmap_text, current_phase_id)
    if not next_phase:
        click.echo(
            f"Cannot find a phase after {current_phase_id} in road_map.md.",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"Current phase {current_phase_id} is complete.")
    click.echo(f"Next phase from roadmap: {next_phase['title']}")

    # Read context files for Claude
    completed_phase_md = (sot_dir / "current_phase.md").read_text()

    vision_md = ""
    vision_path = sot_dir / "vision.md"
    if vision_path.exists():
        vision_md = vision_path.read_text()

    decisions_md = ""
    decisions_path = sot_dir / "decisions.md"
    if decisions_path.exists():
        decisions_md = decisions_path.read_text()

    # Call Claude to generate task breakdown
    config = load_config()
    model = config.agents.designer_model

    try:
        task_lines = generate_task_breakdown(
            next_phase=next_phase,
            completed_phase_md=completed_phase_md,
            decisions_md=decisions_md,
            vision_md=vision_md,
            model=model,
        )
    except RuntimeError as e:
        click.echo(f"Failed to generate task breakdown: {e}", err=True)
        raise SystemExit(1)

    if not task_lines:
        click.echo("Claude returned no task lines. Generating with placeholder.", err=True)
        task_lines = [f"- [ ] {next_phase['phase_id']}-T1: Define tasks for this phase"]

    # Assemble new current_phase.md
    content = _assemble_phase_file(next_phase, task_lines)

    # Write
    phase_path = sot_dir / "current_phase.md"
    phase_path.write_text(content)

    click.echo(f"\nGenerated draft current_phase.md for {next_phase['phase_id']}:")
    click.echo("─" * 50)
    click.echo(content)
    click.echo("─" * 50)
    click.echo(f"\nEdit {phase_path} if needed, then run 'orch phase approve'.")


@phase_group.command("approve")
def phase_approve_cmd():
    """Mark current draft phase as approved, allowing orch run."""
    project = get_active_project()
    if not project:
        click.echo("No active project. Run 'orch switch <name>' first.", err=True)
        raise SystemExit(1)

    sot_dir = PROJECTS_DIR / project["name"]
    status = get_phase_status(sot_dir)

    if status == "approved":
        click.echo("Phase is already approved.")
        return

    if status != "draft":
        click.echo("No draft phase found. Run 'orch phase next' first.", err=True)
        raise SystemExit(1)

    set_phase_status(sot_dir, "approved")

    phase_info = parse_current_phase(sot_dir)
    click.echo(f"Phase {phase_info.phase_id} approved. You can now run 'orch run'.")


@phase_group.command("status")
def phase_status_cmd():
    """Show current phase status."""
    project = get_active_project()
    if not project:
        click.echo("No active project.", err=True)
        raise SystemExit(1)

    sot_dir = PROJECTS_DIR / project["name"]
    phase_info = parse_current_phase(sot_dir)
    status = get_phase_status(sot_dir)

    click.echo(f"Phase: {phase_info.phase_title or '(none)'}")
    click.echo(f"Status: {status or 'approved (legacy)'}")
    click.echo(f"All done: {phase_info.all_done}")
    if phase_info.next_task_key:
        click.echo(f"Next task: {phase_info.next_task_key} — {phase_info.next_task_desc}")


def _assemble_phase_file(next_phase: dict, task_lines: list[str]) -> str:
    """Assemble current_phase.md content from extracted phase info and task lines."""
    parts = [
        f"# {next_phase['title']}",
        "<!-- status: draft -->",
        "",
        "## Phase Goal",
        next_phase["goal"],
        "",
        "## In Scope",
        next_phase["in_scope"],
        "",
        "## Out of Scope",
        next_phase["out_of_scope"],
        "",
        "## Task Queue",
    ]
    parts.extend(task_lines)
    parts.append("")

    return "\n".join(parts)
