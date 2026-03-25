from orch.providers.base import LLMProvider, LLMResponse

# Pricing per million tokens (kimi-k2.5)
_INPUT_CACHE_MISS_PER_MTK = 0.60
_INPUT_CACHE_HIT_PER_MTK = 0.10
_OUTPUT_PER_MTK = 3.00


class KimiProvider(LLMProvider):
    """Kimi K2.5 via OpenAI-compatible API (api.moonshot.cn)."""

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

    def complete(self, system_prompt: str, messages: list[dict],
                 cache_key: str | None = None) -> LLMResponse:
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        kwargs: dict = dict(
            model=self._model,
            messages=full_messages,
            max_completion_tokens=8192,
            # kimi-k2.5: temperature/top_p/presence_penalty are fixed, must NOT be passed
        )

        # prompt_cache_key improves cache hit rate (e.g. pass round_id)
        if cache_key:
            kwargs["extra_body"] = {"prompt_cache_key": cache_key}

        response = self._client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

        # Conservative cost estimate (assume cache miss)
        cost = (input_tokens / 1_000_000 * _INPUT_CACHE_MISS_PER_MTK +
                output_tokens / 1_000_000 * _OUTPUT_PER_MTK)

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
