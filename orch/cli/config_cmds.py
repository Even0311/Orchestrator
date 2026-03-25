import click
import yaml

from orch.config.settings import load_config, set_config_value, CONFIG_PATH


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
    Examples:
      orch config set agents.designer chatgpt
      orch config set agents.reviewer opus
      orch config set agents.executor_model sonnet
      orch config set api_keys.anthropic sk-ant-...
      orch config set notification.email.smtp_host smtp.gmail.com
      orch config set notification.email.from_addr you@email.com
      orch config set notification.email.to_addr you@email.com
    """
    try:
        result = set_config_value(key, value)
        click.echo(f"✓ {result}")
        click.echo(f"  Saved to {CONFIG_PATH}")
    except ValueError as e:
        raise click.ClickException(str(e))


@config_group.command("show")
def config_show():
    """Show current configuration."""
    config = load_config()
    data = config.model_dump(exclude_none=True)

    # Mask API keys
    if "api_keys" in data:
        for k, v in data["api_keys"].items():
            if v:
                data["api_keys"][k] = v[:8] + "..." if len(v) > 8 else "***"

    click.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True))
