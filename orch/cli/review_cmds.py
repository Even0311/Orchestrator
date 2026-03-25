from pathlib import Path

import click

from orch.db.database import get_active_project, get_connection, init_db


@click.command("review")
def review_cmd():
    """Show escalated rounds waiting for your decision."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, escalation_reason, cost_usd, created_at FROM rounds "
            "WHERE project_id = ? AND status = 'escalated' ORDER BY created_at",
            (project["id"],),
        ).fetchall()

    if not rows:
        click.echo("No escalated rounds. Everything is running or complete.")
        return

    state_dir = Path(project["state_dir"])

    for row in rows:
        round_id = row["id"]
        click.echo(f"\n{'!'*60}")
        click.echo(f"  Escalated round: {round_id}")
        click.echo(f"{'!'*60}")

        # Try to show phase dir
        for phase_dir in sorted((state_dir / "phases").iterdir()) if (state_dir / "phases").exists() else []:
            audit_path = phase_dir / round_id / "audit.md"
            if audit_path.exists():
                click.echo(f"\n{audit_path.read_text()}")
                break
        else:
            click.echo(f"\nReason:\n{row['escalation_reason']}")

        click.echo(f"\nRun: orch decide '<instruction to resume>'")


@click.command("decide")
@click.argument("instruction")
def decide_cmd(instruction: str):
    """Provide a decision on the oldest escalated round and resume execution."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM rounds WHERE project_id = ? AND status = 'escalated' ORDER BY created_at LIMIT 1",
            (project["id"],),
        ).fetchone()

    if not row:
        raise click.ClickException("No escalated rounds to decide on.")

    round_id = row["id"]

    # Update current_phase.md with the user's instruction
    state_dir = Path(project["state_dir"])
    phase_path = state_dir / "current_phase.md"
    existing = phase_path.read_text() if phase_path.exists() else ""
    phase_path.write_text(
        existing + f"\n\n## Human Decision ({round_id})\n{instruction}\n"
    )

    # Mark round as resolved
    with get_connection() as conn:
        conn.execute(
            "UPDATE rounds SET status = 'resolved_by_human', updated_at = datetime('now') WHERE id = ?",
            (round_id,),
        )

    click.echo(f"✓ Decision recorded for {round_id}")
    click.echo(f"  Resuming... (run 'orch run' to continue)")
