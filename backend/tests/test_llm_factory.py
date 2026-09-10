import pytest

from app.llm.factory import get_llm_provider
from app.llm.ollama_provider import OllamaLLMProvider


def test_llm_factory_returns_ollama():
    get_llm_provider.cache_clear()

    provider = get_llm_provider()

    assert isinstance(
        provider,
        OllamaLLMProvider,
    )


def test_llm_factory_uses_configured_model():
    get_llm_provider.cache_clear()

    provider = get_llm_provider()

    assert provider.model == "qwen2.5:7b"


def test_llm_factory_uses_configured_base_url():
    get_llm_provider.cache_clear()

    provider = get_llm_provider()

    assert (
        provider.base_url
        == "http://127.0.0.1:11434"
    )


def test_llm_factory_uses_configured_timeout():
    get_llm_provider.cache_clear()

    provider = get_llm_provider()

    assert provider.timeout == 120.0


def test_llm_factory_returns_cached_instance():
    get_llm_provider.cache_clear()

    first = get_llm_provider()
    second = get_llm_provider()

    assert first is second


def test_llm_factory_rejects_unsupported_provider(
    monkeypatch,
):
    from app.llm import factory

    get_llm_provider.cache_clear()

    monkeypatch.setattr(
        factory.settings,
        "llm_provider",
        "unsupported",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider",
    ):
        get_llm_provider()

    get_llm_provider.cache_clear()
