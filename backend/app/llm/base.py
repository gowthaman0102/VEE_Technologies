from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        response_format: dict[str, Any] | str | None = None,
    ) -> LLMResult:
        raise NotImplementedError
