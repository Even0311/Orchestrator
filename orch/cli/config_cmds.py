import os

import click
import yaml

from orch.config.settings import (
    load_config, set_config_value, CONFIG_PATH, ENV_PATH,
    VALID_CLAUDE_MODELS,
)


@click.group("config")
def config_group():
    """Manage global orchestrator configuration."""
    pass


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value.

    \b
    Agent model:
      orch config set agents.executor_model  sonnet|opus|haiku

    \b
    Email notification:
      orch config set notification.email.smtp_host  smtp.gmail.com
      orch config set notification.email.smtp_port  587
      orch config set notification.email.from_addr  you@email.com
      orch config set notification.email.to_addr    you@email.com
    """
    try:
        result = set_config_value(key, value)
        click.echo(f"  {result}")
    except ValueError as e:
        raise click.ClickException(str(e))


@config_group.command("show")
def config_show():
    """Show current configuration."""
    config = load_config()
    data = config.model_dump(exclude_none=True)

    click.echo("=== Config (config.yaml) ===")
    click.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True).rstrip())

    click.echo(f"\nValid Claude models: {', '.join(VALID_CLAUDE_MODELS)}")
    click.echo(f"Config file: {CONFIG_PATH}")
