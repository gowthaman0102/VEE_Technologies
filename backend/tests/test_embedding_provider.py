from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.embeddings.openai_provider import OpenAIEmbeddingProvider


@pytest.mark.asyncio
async def test_embed_text_returns_embedding_result():
    dimensions = 4

    client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=AsyncMock(
                return_value=SimpleNamespace(
                    data=[
                        SimpleNamespace(
                            embedding=[0.1, 0.2, 0.3, 0.4]
                        )
                    ]
                )
            )
        )
    )

    provider = OpenAIEmbeddingProvider(
        client=client,
        model="test-embedding-model",
        dimensions=dimensions,
    )

    result = await provider.embed_text("PayU payments in India")

    assert result.vector == [0.1, 0.2, 0.3, 0.4]
    assert result.model == "test-embedding-model"
    assert result.dimensions == 4

    client.embeddings.create.assert_awaited_once_with(
        model="test-embedding-model",
        input="PayU payments in India",
        dimensions=4,
        encoding_format="float",
    )


@pytest.mark.asyncio
async def test_embed_text_strips_whitespace():
    client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=AsyncMock(
                return_value=SimpleNamespace(
                    data=[SimpleNamespace(embedding=[0.1, 0.2])]
                )
            )
        )
    )

    provider = OpenAIEmbeddingProvider(
        client=client,
        model="test-model",
        dimensions=2,
    )

    await provider.embed_text("  PayU regulation  ")

    client.embeddings.create.assert_awaited_once_with(
        model="test-model",
        input="PayU regulation",
        dimensions=2,
        encoding_format="float",
    )


@pytest.mark.asyncio
async def test_embed_text_rejects_empty_input():
    client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=AsyncMock()
        )
    )

    provider = OpenAIEmbeddingProvider(
        client=client,
        dimensions=2,
    )

    with pytest.raises(
        ValueError,
        match="Embedding input cannot be empty",
    ):
        await provider.embed_text("   ")

    client.embeddings.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_embed_text_rejects_empty_provider_response():
    client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=AsyncMock(
                return_value=SimpleNamespace(data=[])
            )
        )
    )

    provider = OpenAIEmbeddingProvider(
        client=client,
        dimensions=2,
    )

    with pytest.raises(
        RuntimeError,
        match="returned no embedding data",
    ):
        await provider.embed_text("PayU")


@pytest.mark.asyncio
async def test_embed_text_rejects_wrong_dimension():
    client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=AsyncMock(
                return_value=SimpleNamespace(
                    data=[
                        SimpleNamespace(
                            embedding=[0.1, 0.2, 0.3]
                        )
                    ]
                )
            )
        )
    )

    provider = OpenAIEmbeddingProvider(
        client=client,
        dimensions=2,
    )

    with pytest.raises(
        RuntimeError,
        match="unexpected vector dimension",
    ):
        await provider.embed_text("PayU")


def test_provider_rejects_invalid_dimensions():
    client = SimpleNamespace()

    with pytest.raises(
        ValueError,
        match="must be greater than zero",
    ):
        OpenAIEmbeddingProvider(
            client=client,
            dimensions=0,
        )


def test_provider_requires_api_key_without_injected_client(monkeypatch):
    monkeypatch.setattr(
        "app.embeddings.openai_provider.settings.openai_api_key",
        None,
    )

    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required",
    ):
        OpenAIEmbeddingProvider()
