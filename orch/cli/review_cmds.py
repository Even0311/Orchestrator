import click

from orch.db.database import get_active_project, init_db


@click.command("review")
def review_cmd():
    """Show the escalation report waiting for your decision."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")
    click.echo(f"[TODO Phase 5] Would show pending escalation report for '{project['name']}'")


@click.command("decide")
@click.argument("decision", required=False)
def decide_cmd(decision: str):
    """Provide a decision on a pending escalation and resume execution."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")
    click.echo(f"[TODO Phase 5] Would apply decision and resume '{project['name']}'")
