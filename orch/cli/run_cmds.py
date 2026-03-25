import click

from orch.db.database import get_active_project, get_connection, init_db


@click.command("run")
def run_cmd():
    """Start the automation loop for the active project."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    from orch.engine.orchestrator import run_project
    run_project(project)


@click.command("status")
def status_cmd():
    """Show the current status of the active project."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    click.echo(f"Project  : {project['name']}")
    click.echo(f"Codebase : {project['codebase_path']}")
    click.echo(f"State    : {project['state_dir']}")

    with get_connection() as conn:
        rounds = conn.execute(
            "SELECT id, status, attempt_count, cost_usd, created_at FROM rounds "
            "WHERE project_id = ? ORDER BY created_at DESC LIMIT 10",
            (project["id"],),
        ).fetchall()

        total_cost = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) as total FROM rounds WHERE project_id = ?",
            (project["id"],),
        ).fetchone()["total"]

    if not rounds:
        click.echo("\nNo rounds yet. Run 'orch run' to start.")
        return

    click.echo(f"\nRecent rounds (total cost: ${total_cost:.4f}):")
    for r in rounds:
        status_icon = {"passed": "✓", "escalated": "!", "pending": "…"}.get(r["status"], "?")
        click.echo(
            f"  {status_icon} {r['id']}  {r['status']:10}  "
            f"attempts:{r['attempt_count']}  ${r['cost_usd']:.4f}"
        )

    with get_connection() as conn:
        pending = conn.execute(
            "SELECT COUNT(*) as cnt FROM rounds WHERE project_id = ? AND status = 'escalated'",
            (project["id"],),
        ).fetchone()["cnt"]

    if pending:
        click.echo(f"\n  ⚠  {pending} escalated round(s) waiting. Run 'orch review'.")
