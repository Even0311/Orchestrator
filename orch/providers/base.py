from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, messages: list[dict]) -> LLMResponse:
        """Send messages and return a response."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
