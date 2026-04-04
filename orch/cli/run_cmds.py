import click

from orch.db.database import get_active_project, get_connection, init_db


ACTIONABLE_HUMAN_STATUSES = (
    "escalated",
    "accepted_by_human",
    "resume_requested",
    "rejected_by_human",
)


@click.command("run")
@click.option("--once", is_flag=True, default=False,
              help="Run a single round then stop (useful for manual inspection).")
def run_cmd(once: bool):
    """Start the automation loop for the active project."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    from orch.engine.orchestrator import run_project
    run_project(project, run_once=once)


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

        actionable = conn.execute(
            "SELECT COUNT(*) as cnt FROM rounds WHERE project_id = ? AND status IN ('escalated', 'accepted_by_human', 'resume_requested', 'rejected_by_human')",
            (project["id"],),
        ).fetchone()["cnt"]

    if not rounds:
        click.echo("\nNo rounds yet. Run 'orch run' to start.")
        return

    status_icon = {
        "passed": "✓",
        "accepted_by_human": "✓",
        "accepted_applied": "✓",
        "escalated": "!",
        "rejected_by_human": "×",
        "redo_consumed": "↺",
        "resume_requested": "↺",
        "resume_consumed": "↺",
        "pending": "…",
    }

    click.echo(f"\nRecent rounds (total cost: ${total_cost:.4f}):")
    for r in rounds:
        icon = status_icon.get(r["status"], "?")
        click.echo(
            f"  {icon} {r['id']}  {r['status']:18}  "
            f"attempts:{r['attempt_count']}  ${r['cost_usd']:.4f}"
        )

    if actionable:
        click.echo(f"\n  ⚠  {actionable} round(s) need human attention or a follow-up run.")
        click.echo("     Use 'orch review' to inspect escalations, then 'orch decide' or 'orch run' as appropriate.")
