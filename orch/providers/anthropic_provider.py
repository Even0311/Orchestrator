from orch.providers.base import LLMProvider, LLMResponse

# Pricing per million tokens (as of 2025)
_OPUS_INPUT_PER_MTK = 15.0
_OPUS_OUTPUT_PER_MTK = 75.0


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    def complete(self, system_prompt: str, messages: list[dict]) -> LLMResponse:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=8096,
            system=system_prompt,
            messages=messages,
        )
        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens / 1_000_000 * _OPUS_INPUT_PER_MTK +
                output_tokens / 1_000_000 * _OPUS_OUTPUT_PER_MTK)
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
