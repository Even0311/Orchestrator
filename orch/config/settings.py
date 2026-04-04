import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

ORCH_HOME = Path.home() / ".orch"
CONFIG_PATH = ORCH_HOME / "config.yaml"

# Orchestrator repo root (next to pyproject.toml)
REPO_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = REPO_ROOT / ".env"
# Legacy external state location kept for backward compatibility only.
PROJECTS_DIR = REPO_ROOT / "projects"

# Repo-local orchestration state (new default)
REPO_STATE_DIRNAME = ".orch"
RUNTIME_SUBDIR = "runtime"
CLAUDE_AGENTS_SUBDIR = Path(".claude") / "agents"

VALID_CLAUDE_MODELS = ("sonnet", "opus", "haiku")


class EmailConfig(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    from_addr: str = ""
    to_addr: str = ""


class NotificationConfig(BaseModel):
    email: Optional[EmailConfig] = None


class AgentConfig(BaseModel):
    executor_model: str = "sonnet"     # Model for round-driver/executor/reviewer
    designer_model: str = "opus"       # Model for designer and phase planning


class OrchestratorConfig(BaseModel):
    agents: AgentConfig = AgentConfig()
    notification: NotificationConfig = NotificationConfig()


def load_env() -> None:
    """Load repo .env into environment variables."""
    from dotenv import load_dotenv
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=False)


def load_config() -> OrchestratorConfig:
    if not CONFIG_PATH.exists():
        return OrchestratorConfig()
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f) or {}
    return OrchestratorConfig(**data)


def save_config(config: OrchestratorConfig) -> None:
    ORCH_HOME.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(
            config.model_dump(exclude_none=True),
            f,
            default_flow_style=False,
            allow_unicode=True,
        )


def get_repo_state_dir(codebase_path: str | Path) -> Path:
    """Return the repo-local orchestration state directory for a target codebase."""
    return Path(codebase_path).resolve() / REPO_STATE_DIRNAME


def get_runtime_dir(codebase_path: str | Path) -> Path:
    """Return the transient runtime docs directory under the repo-local state dir."""
    return get_repo_state_dir(codebase_path) / RUNTIME_SUBDIR


def set_config_value(key: str, value: str) -> str:
    """Set a config value by dot-notation key. Returns a description of the change."""
    config = load_config()
    parts = key.split(".")

    if parts[0] == "agents":
        if parts[1] in ("executor_model", "model"):
            if value not in VALID_CLAUDE_MODELS:
                raise ValueError(f"Invalid model '{value}'. Choose from: {', '.join(VALID_CLAUDE_MODELS)}")
            config.agents.executor_model = value
        elif parts[1] == "designer_model":
            if value not in VALID_CLAUDE_MODELS:
                raise ValueError(f"Invalid model '{value}'. Choose from: {', '.join(VALID_CLAUDE_MODELS)}")
            config.agents.designer_model = value
        else:
            raise ValueError(f"Unknown agents key: {parts[1]}. Available: executor_model, designer_model")

    elif parts[0] == "notification" and parts[1] == "email":
        if config.notification.email is None:
            config.notification.email = EmailConfig()
        email = config.notification.email
        if parts[2] not in {"smtp_host", "smtp_port", "from_addr", "to_addr"}:
            raise ValueError(f"Unknown notification.email key: {parts[2]}")
        if parts[2] == "smtp_port":
            setattr(email, parts[2], int(value))
        else:
            setattr(email, parts[2], value)
    else:
        raise ValueError(
            f"Unknown config key: {key}\n"
            f"  API keys are set in {ENV_PATH} — see 'orch config show'"
        )

    save_config(config)
    return f"{key} = {value}"
