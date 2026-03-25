import os

import click
import yaml

from orch.config.settings import (
    load_config, set_config_value, CONFIG_PATH, ENV_PATH,
    VALID_DESIGNER_MODELS, VALID_REVIEWER_MODELS, VALID_EXECUTOR_MODELS,
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
    Agent model options:
      orch config set agents.designer   opus|chatgpt|minimax
      orch config set agents.reviewer   opus|chatgpt|minimax
      orch config set agents.executor_model  sonnet|opus|haiku

    \b
    Email notification:
      orch config set notification.email.smtp_host  smtp.gmail.com
      orch config set notification.email.smtp_port  587
      orch config set notification.email.from_addr  you@email.com
      orch config set notification.email.to_addr    you@email.com

    \b
    API keys and routes are set in ~/.orch/.env — see 'orch config show'.
    """
    try:
        result = set_config_value(key, value)
        click.echo(f"✓ {result}")
    except ValueError as e:
        raise click.ClickException(str(e))


@config_group.command("show")
def config_show():
    """Show current configuration and .env key status."""
    config = load_config()
    data = config.model_dump(exclude_none=True)

    click.echo("=== Agent config (config.yaml) ===")
    click.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True).rstrip())

    click.echo(f"\n=== API keys & routes ({ENV_PATH}) ===")
    env_vars = {
        "ANTHROPIC_API_KEY": "required for designer/reviewer = opus",
        "OPENAI_API_KEY":    "required for designer/reviewer = chatgpt",
        "MINIMAX_API_KEY":   "required for designer/reviewer = minimax",
        "MINIMAX_BASE_URL":  "optional, default: https://api.minimax.chat/v1",
    }
    for var, note in env_vars.items():
        val = os.environ.get(var)
        if val:
            masked = val[:8] + "..." if len(val) > 8 else "***"
            status = f"✓ {masked}"
        else:
            status = "✗ not set"
        click.echo(f"  {var:<22} {status}   ({note})")

    if not ENV_PATH.exists():
        click.echo(f"\n  Hint: create {ENV_PATH} with your keys:")
        click.echo(f"    ANTHROPIC_API_KEY=sk-ant-...")
        click.echo(f"    OPENAI_API_KEY=sk-...")
        click.echo(f"    MINIMAX_API_KEY=...")
        click.echo(f"    MINIMAX_BASE_URL=https://api.minimax.chat/v1  # optional")
