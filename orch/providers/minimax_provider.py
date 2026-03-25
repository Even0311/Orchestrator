from orch.providers.base import LLMProvider, LLMResponse


class MiniMaxProvider(LLMProvider):
    """MiniMax via OpenAI-compatible API."""

    BASE_URL = "https://api.minimax.chat/v1"

    def __init__(self, api_key: str, model: str = "abab6.5s-chat"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
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
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,  # MiniMax pricing varies; tracked by token count
        )
