import click

from orch.config.settings import load_env
from orch.db.database import init_db
from orch.cli.project_cmds import new_cmd, list_cmd, switch_cmd, set_path_cmd
from orch.cli.config_cmds import config_group
from orch.cli.run_cmds import run_cmd, status_cmd
from orch.cli.review_cmds import review_cmd, decide_cmd
from orch.cli.log_cmds import log_cmd


@click.group()
def cli():
    """Orchestrator — AI-assisted development workflow manager."""
    load_env()
    init_db()


cli.add_command(new_cmd)
cli.add_command(list_cmd)
cli.add_command(switch_cmd)
cli.add_command(set_path_cmd)
cli.add_command(config_group)
cli.add_command(run_cmd)
cli.add_command(status_cmd)
cli.add_command(review_cmd)
cli.add_command(decide_cmd)
cli.add_command(log_cmd)
