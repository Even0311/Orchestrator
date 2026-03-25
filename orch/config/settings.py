from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

ORCH_HOME = Path.home() / ".orch"
CONFIG_PATH = ORCH_HOME / "config.yaml"

VALID_DESIGNER_MODELS = ("opus", "chatgpt", "minimax")
VALID_REVIEWER_MODELS = ("opus", "chatgpt", "minimax")
VALID_EXECUTOR_MODELS = ("sonnet", "opus", "haiku")


class EmailConfig(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    from_addr: str = ""
    to_addr: str = ""


class NotificationConfig(BaseModel):
    email: Optional[EmailConfig] = None


class AgentConfig(BaseModel):
    designer: str = "opus"
    reviewer: str = "opus"
    executor_model: str = "sonnet"


class ApiKeys(BaseModel):
    anthropic: Optional[str] = None
    openai: Optional[str] = None
    minimax: Optional[str] = None


class OrchestratorConfig(BaseModel):
    agents: AgentConfig = AgentConfig()
    api_keys: ApiKeys = ApiKeys()
    notification: NotificationConfig = NotificationConfig()


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


def set_config_value(key: str, value: str) -> str:
    """Set a config value by dot-notation key. Returns a description of the change."""
    config = load_config()

    parts = key.split(".")
    if parts[0] == "agents":
        if parts[1] == "designer":
            if value not in VALID_DESIGNER_MODELS:
                raise ValueError(f"Invalid designer model '{value}'. Choose from: {', '.join(VALID_DESIGNER_MODELS)}")
            config.agents.designer = value
        elif parts[1] == "reviewer":
            if value not in VALID_REVIEWER_MODELS:
                raise ValueError(f"Invalid reviewer model '{value}'. Choose from: {', '.join(VALID_REVIEWER_MODELS)}")
            config.agents.reviewer = value
        elif parts[1] == "executor_model":
            if value not in VALID_EXECUTOR_MODELS:
                raise ValueError(f"Invalid executor model '{value}'. Choose from: {', '.join(VALID_EXECUTOR_MODELS)}")
            config.agents.executor_model = value
        else:
            raise ValueError(f"Unknown agents key: {parts[1]}")

    elif parts[0] == "api_keys":
        if parts[1] == "anthropic":
            config.api_keys.anthropic = value
        elif parts[1] == "openai":
            config.api_keys.openai = value
        elif parts[1] == "minimax":
            config.api_keys.minimax = value
        else:
            raise ValueError(f"Unknown api_keys key: {parts[1]}")

    elif parts[0] == "notification" and parts[1] == "email":
        if config.notification.email is None:
            from orch.config.settings import EmailConfig
            config.notification.email = EmailConfig()
        email = config.notification.email
        if parts[2] == "smtp_host":
            email.smtp_host = value
        elif parts[2] == "smtp_port":
            email.smtp_port = int(value)
        elif parts[2] == "from_addr":
            email.from_addr = value
        elif parts[2] == "to_addr":
            email.to_addr = value
        else:
            raise ValueError(f"Unknown notification.email key: {parts[2]}")
    else:
        raise ValueError(f"Unknown config key: {key}")

    save_config(config)
    return f"{key} = {value}"
