from pathlib import Path

import click

from orch.db.database import get_active_project, get_connection, init_db


@click.command("log")
@click.argument("round_id", required=False)
def log_cmd(round_id: str):
    """Show round history, or a specific round's audit report."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    if round_id:
        _show_round_detail(project, round_id)
    else:
        _show_round_list(project)


def _show_round_list(project) -> None:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, status, attempt_count, cost_usd, created_at FROM rounds "
            "WHERE project_id = ? ORDER BY created_at",
            (project["id"],),
        ).fetchall()

    if not rows:
        click.echo("No rounds yet.")
        return

    click.echo(f"Rounds for '{project['name']}':\n")
    icons = {"passed": "✓", "escalated": "!", "resolved_by_human": "H", "pending": "…"}
    for r in rows:
        icon = icons.get(r["status"], "?")
        click.echo(
            f"  {icon} {r['id']}  {r['status']:20}  "
            f"attempts:{r['attempt_count']}  ${r['cost_usd']:.4f}  {r['created_at'][:16]}"
        )


def _show_round_detail(project, round_id: str) -> None:
    state_dir = Path(project["state_dir"])

    # Find the audit file
    phases_dir = state_dir / "phases"
    if phases_dir.exists():
        for phase_dir in sorted(phases_dir.iterdir()):
            audit_path = phase_dir / round_id / "audit.md"
            if audit_path.exists():
                click.echo(audit_path.read_text())

                # Also show attempt files
                for attempt_file in sorted((phase_dir / round_id).glob("attempt_*.md")):
                    click.echo(f"\n{'─'*60}\n")
                    click.echo(attempt_file.read_text())
                return

    # Fallback to DB
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM rounds WHERE id = ? AND project_id = ?",
            (round_id, project["id"]),
        ).fetchone()

    if not row:
        raise click.ClickException(f"Round '{round_id}' not found.")

    click.echo(f"Round: {row['id']}")
    click.echo(f"Status: {row['status']}")
    click.echo(f"Attempts: {row['attempt_count']}")
    click.echo(f"Cost: ${row['cost_usd']:.4f}")
    if row["escalation_reason"]:
        click.echo(f"\nEscalation reason:\n{row['escalation_reason']}")
