from pathlib import Path

import click

from orch.db.database import get_active_project, get_round, get_connection, init_db
from orch.utils.git_ops import is_clean, reset_hard, GitError


@click.command("rollback")
@click.argument("round_id")
@click.option("--force", is_flag=True, help="Skip clean-working-tree check")
def rollback_cmd(round_id: str, force: bool):
    """Roll back both orchestrator and target project to a specific round.

    Both repos are hard-reset to the commits recorded at that round.
    Any work done after that round will be lost from the branch
    (still recoverable via git reflog).

    \b
    Example:
      orch rollback round-0003
    """
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    row = get_round(round_id)
    if not row:
        raise click.ClickException(f"Round '{round_id}' not found.")

    orch_hash = row["orchestrator_commit"]
    target_hash = row["target_commit"]

    if not orch_hash or not target_hash:
        raise click.ClickException(
            f"Round '{round_id}' has no commit hashes recorded. "
            "Only rounds completed after the rollback feature was added can be rolled back."
        )

    from orch.config.settings import REPO_ROOT
    orch_repo = REPO_ROOT
    target_repo = Path(project["codebase_path"])

    # Safety: both repos must be clean unless --force
    if not force:
        if not is_clean(orch_repo):
            raise click.ClickException(
                "Orchestrator repo has uncommitted changes. "
                "Commit or stash them first, or use --force."
            )
        if not is_clean(target_repo):
            raise click.ClickException(
                f"Target project has uncommitted changes in {target_repo}. "
                "Commit or stash them first, or use --force."
            )

    click.echo(f"\nRolling back to {round_id}:")
    click.echo(f"  Orchestrator → {orch_hash[:12]}")
    click.echo(f"  Target       → {target_hash[:12]}")
    click.confirm("\nThis will hard-reset both repos. Continue?", abort=True)

    try:
        reset_hard(orch_repo, orch_hash)
        click.echo(f"  ✓ Orchestrator reset to {orch_hash[:7]}")
    except GitError as e:
        raise click.ClickException(f"Orchestrator rollback failed: {e}")

    try:
        reset_hard(target_repo, target_hash)
        click.echo(f"  ✓ Target project reset to {target_hash[:7]}")
    except GitError as e:
        raise click.ClickException(
            f"Target project rollback failed: {e}\n"
            f"  ⚠ Orchestrator was already reset — use 'git reflog' to recover if needed."
        )

    # Update DB: mark rounds after this one as rolled_back
    with get_connection() as conn:
        conn.execute(
            "UPDATE rounds SET status = 'rolled_back' "
            "WHERE project_id = ? AND created_at > "
            "(SELECT created_at FROM rounds WHERE id = ?)",
            (project["id"], round_id),
        )

    click.echo(f"\n✓ Rollback complete. Both repos are at {round_id}.")
    click.echo(f"  Run 'orch run' to continue from this point.")
