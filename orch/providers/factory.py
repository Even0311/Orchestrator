from orch.providers.base import LLMProvider
from orch.config.settings import OrchestratorConfig


def get_provider(role: str, config: OrchestratorConfig) -> LLMProvider:
    """Instantiate the correct provider for a given role (designer/reviewer)."""
    model_key = config.agents.designer if role == "designer" else config.agents.reviewer

    if model_key == "opus":
        api_key = config.api_keys.anthropic
        if not api_key:
            raise ValueError(
                "Anthropic API key not configured. Run: orch config set api_keys.anthropic <key>"
            )
        from orch.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=api_key)

    elif model_key == "chatgpt":
        api_key = config.api_keys.openai
        if not api_key:
            raise ValueError(
                "OpenAI API key not configured. Run: orch config set api_keys.openai <key>"
            )
        from orch.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key)

    elif model_key == "minimax":
        api_key = config.api_keys.minimax
        if not api_key:
            raise ValueError(
                "MiniMax API key not configured. Run: orch config set api_keys.minimax <key>"
            )
        from orch.providers.minimax_provider import MiniMaxProvider
        return MiniMaxProvider(api_key=api_key)

    else:
        raise ValueError(f"Unknown model key '{model_key}' for role '{role}'")
