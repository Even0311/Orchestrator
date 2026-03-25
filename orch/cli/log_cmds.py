import click

from orch.db.database import get_active_project, init_db


@click.command("log")
@click.argument("round_id", required=False)
def log_cmd(round_id: str):
    """Show round history, or a specific round's audit report."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    if round_id:
        click.echo(f"[TODO Phase 7] Would show audit report for round '{round_id}'")
    else:
        click.echo(f"[TODO Phase 7] Would list all rounds for '{project['name']}'")
