from orch.providers.base import LLMProvider
from orch.config.settings import OrchestratorConfig, get_api_key, get_minimax_base_url


def get_provider(role: str, config: OrchestratorConfig) -> LLMProvider:
    """Instantiate the correct provider for a given role (designer/reviewer)."""
    model_key = config.agents.designer if role == "designer" else config.agents.reviewer

    if model_key == "opus":
        api_key = get_api_key("anthropic")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Add it to ~/.orch/.env"
            )
        from orch.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=api_key)

    elif model_key == "chatgpt":
        api_key = get_api_key("openai")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Add it to ~/.orch/.env"
            )
        from orch.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key)

    elif model_key == "minimax":
        api_key = get_api_key("minimax")
        if not api_key:
            raise ValueError(
                "MINIMAX_API_KEY not set. Add it to ~/.orch/.env"
            )
        from orch.providers.minimax_provider import MiniMaxProvider
        return MiniMaxProvider(api_key=api_key, base_url=get_minimax_base_url())

    else:
        raise ValueError(f"Unknown model key '{model_key}' for role '{role}'")
