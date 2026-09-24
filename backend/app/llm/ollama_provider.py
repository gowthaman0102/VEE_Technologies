from typing import Any

import httpx

from app.llm.base import LLMProvider, LLMResult


class OllamaLLMProvider(LLMProvider):
    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 120.0,
        temperature: float = 0.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = temperature

    async def generate(
        self,
        prompt: str,
        *,
        response_format: dict[str, Any] | str | None = None,
    ) -> LLMResult:
        normalized_prompt = prompt.strip()

        if not normalized_prompt:
            raise ValueError("Prompt cannot be empty.")

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": normalized_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        if response_format is not None:
            payload["format"] = response_format

        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

        text = str(
            data.get("response", "")
        ).strip()

        if not text:
            raise ValueError(
                "Ollama returned an empty response."
            )

        return LLMResult(
            text=text,
            model=str(
                data.get("model", self.model)
            ),
        )
