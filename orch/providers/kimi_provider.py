from orch.providers.base import LLMProvider, LLMResponse

# Pricing per million tokens (kimi-k2.5)
_INPUT_CACHE_MISS_PER_MTK = 0.60
_INPUT_CACHE_HIT_PER_MTK = 0.10
_OUTPUT_PER_MTK = 3.00


class KimiProvider(LLMProvider):
    """Kimi K2.5 via OpenAI-compatible API."""

    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "kimi-k2.5"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL,
                 base_url: str = DEFAULT_BASE_URL):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    def complete(self, system_prompt: str, messages: list[dict]) -> LLMResponse:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = self._client.chat.completions.create(
            model=self._model,
            messages=full_messages,
        )
        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        # Assume cache miss for cost estimate (conservative)
        cost = (input_tokens / 1_000_000 * _INPUT_CACHE_MISS_PER_MTK +
                output_tokens / 1_000_000 * _OUTPUT_PER_MTK)
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
