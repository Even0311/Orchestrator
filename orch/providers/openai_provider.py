from orch.providers.base import LLMProvider, LLMResponse

# Pricing per million tokens (gpt-4o as of 2025)
_GPT4O_INPUT_PER_MTK = 2.50
_GPT4O_OUTPUT_PER_MTK = 10.0


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        self._client = OpenAI(api_key=api_key)
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
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens / 1_000_000 * _GPT4O_INPUT_PER_MTK +
                output_tokens / 1_000_000 * _GPT4O_OUTPUT_PER_MTK)
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
