from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.llm.ollama_provider import OllamaLLMProvider


@pytest.mark.asyncio
async def test_ollama_generate_success(monkeypatch):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "model": "qwen2.5:7b",
        "response": "Generated response",
    }

    post_mock = AsyncMock(
        return_value=response
    )

    client = AsyncMock()
    client.post = post_mock

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client

    monkeypatch.setattr(
        "app.llm.ollama_provider.httpx.AsyncClient",
        MagicMock(return_value=context_manager),
    )

    provider = OllamaLLMProvider(
        model="qwen2.5:7b",
        base_url="http://127.0.0.1:11434",
        timeout=30.0,
    )

    result = await provider.generate(
        "Test prompt"
    )

    assert result.text == "Generated response"
    assert result.model == "qwen2.5:7b"

    post_mock.assert_awaited_once()

    _, kwargs = post_mock.call_args

    assert kwargs["json"] == {
        "model": "qwen2.5:7b",
        "prompt": "Test prompt",
        "stream": False,
    }


@pytest.mark.asyncio
async def test_ollama_generate_with_response_format(
    monkeypatch,
):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "model": "qwen2.5:7b",
        "response": '{"value":"ok"}',
    }

    post_mock = AsyncMock(
        return_value=response
    )

    client = AsyncMock()
    client.post = post_mock

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client

    monkeypatch.setattr(
        "app.llm.ollama_provider.httpx.AsyncClient",
        MagicMock(return_value=context_manager),
    )

    provider = OllamaLLMProvider()

    schema = {
        "type": "object",
        "properties": {
            "value": {
                "type": "string"
            }
        },
        "required": [
            "value"
        ],
    }

    await provider.generate(
        "Structured prompt",
        response_format=schema,
    )

    _, kwargs = post_mock.call_args

    assert kwargs["json"]["format"] == schema


@pytest.mark.asyncio
async def test_ollama_generate_rejects_empty_prompt():
    provider = OllamaLLMProvider()

    with pytest.raises(
        ValueError,
        match="Prompt cannot be empty",
    ):
        await provider.generate("   ")


@pytest.mark.asyncio
async def test_ollama_generate_rejects_empty_response(
    monkeypatch,
):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "model": "qwen2.5:7b",
        "response": "   ",
    }

    client = AsyncMock()
    client.post = AsyncMock(
        return_value=response
    )

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client

    monkeypatch.setattr(
        "app.llm.ollama_provider.httpx.AsyncClient",
        MagicMock(return_value=context_manager),
    )

    provider = OllamaLLMProvider()

    with pytest.raises(
        ValueError,
        match="Ollama returned an empty response",
    ):
        await provider.generate(
            "Test prompt"
        )


@pytest.mark.asyncio
async def test_ollama_generate_propagates_http_error(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/generate",
    )

    response = httpx.Response(
        status_code=500,
        request=request,
    )

    mocked_response = MagicMock()

    mocked_response.raise_for_status.side_effect = (
        httpx.HTTPStatusError(
            "Server error",
            request=request,
            response=response,
        )
    )

    client = AsyncMock()
    client.post = AsyncMock(
        return_value=mocked_response
    )

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client

    monkeypatch.setattr(
        "app.llm.ollama_provider.httpx.AsyncClient",
        MagicMock(return_value=context_manager),
    )

    provider = OllamaLLMProvider()

    with pytest.raises(
        httpx.HTTPStatusError
    ):
        await provider.generate(
            "Test prompt"
        )
