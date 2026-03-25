import click

from orch.db.database import get_active_project, init_db


@click.command("run")
def run_cmd():
    """Start the automation loop for the active project."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")
    click.echo(f"[TODO Phase 5] Would run automation loop for '{project['name']}'")


@click.command("status")
def status_cmd():
    """Show the current status of the active project."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")
    click.echo(f"Active project : {project['name']}")
    click.echo(f"Codebase       : {project['codebase_path']}")
    click.echo(f"State dir      : {project['state_dir']}")
    click.echo(f"\n[TODO Phase 5] Phase/round status coming in Phase 5")
