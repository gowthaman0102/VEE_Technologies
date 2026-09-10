from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.llm import LLMResult
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)
from app.services.rag_context_service import RAGContext
from app.services.article_triage_service import (
    triage_article,
)


def make_article():
    return SimpleNamespace(
        id=8,
        title="PayU receives RBI approval",
        source_name="test-source",
        cleaned_content=(
            "PayU received final approval from RBI "
            "to operate as a payment aggregator."
        ),
    )


def make_context():
    return CompanySemanticContext(
        company_id=1,
        company_name="PayU",
        text=(
            "Company: PayU\n"
            "Industry: Fintech / Payments\n"
            "Regulators: RBI"
        ),
    )


def make_rag_context():
    return RAGContext(
        query="PayU: PayU receives RBI approval",
        related_articles=[],
    )


def make_provider(response_text: str):
    return SimpleNamespace(
        generate=AsyncMock(
            return_value=LLMResult(
                text=response_text,
                model="test-llm",
            )
        )
    )


def patch_common(monkeypatch):
    monkeypatch.setattr(
        "app.services.article_triage_service.get_article",
        AsyncMock(return_value=make_article()),
    )

    monkeypatch.setattr(
        "app.services.article_triage_service."
        "build_company_semantic_context",
        AsyncMock(return_value=make_context()),
    )

    monkeypatch.setattr(
        "app.services.article_triage_service."
        "retrieve_rag_context",
        AsyncMock(return_value=make_rag_context()),
    )

    monkeypatch.setattr(
        "app.services.article_triage_service."
        "save_article_triage",
        AsyncMock(),
    )


@pytest.mark.asyncio
async def test_triage_article_success(monkeypatch):
    patch_common(monkeypatch)

    provider = make_provider(
        """
        {
          "company_name": "PayU",
          "event_type": "regulatory_action",
          "summary": "PayU received final RBI approval.",
          "why_it_matters": "The approval supports regulated operations.",
          "evidence": [
            "PayU received final approval from RBI."
          ],
          "potential_impact": "PayU can expand regulated payment services.",
          "urgency": "high",
          "confidence": 0.9
        }
        """
    )

    result = await triage_article(
        AsyncMock(),
        article_id=8,
        company_id=1,
        provider=provider,
    )

    assert result is not None
    assert result.article_id == 8
    assert result.model == "test-llm"
    assert result.triage.company_name == "PayU"
    assert result.triage.event_type == "regulatory_action"
    assert result.triage.urgency == "high"
    assert result.triage.confidence == 0.9

    provider.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_triage_article_missing_article(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.article_triage_service.get_article",
        AsyncMock(return_value=None),
    )

    provider = make_provider("{}")

    with pytest.raises(
        ValueError,
        match="Article 999 not found",
    ):
        await triage_article(
            AsyncMock(),
            article_id=999,
            company_id=1,
            provider=provider,
        )

    provider.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_triage_article_missing_company(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.article_triage_service.get_article",
        AsyncMock(return_value=make_article()),
    )

    monkeypatch.setattr(
        "app.services.article_triage_service."
        "build_company_semantic_context",
        AsyncMock(return_value=None),
    )

    provider = make_provider("{}")

    with pytest.raises(
        ValueError,
        match="Company 999 not found",
    ):
        await triage_article(
            AsyncMock(),
            article_id=8,
            company_id=999,
            provider=provider,
        )

    provider.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_triage_article_invalid_json(
    monkeypatch,
):
    patch_common(monkeypatch)

    provider = make_provider(
        "This is not JSON."
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        await triage_article(
            AsyncMock(),
            article_id=8,
            company_id=1,
            provider=provider,
        )


@pytest.mark.asyncio
async def test_triage_article_schema_validation_failure(
    monkeypatch,
):
    patch_common(monkeypatch)

    provider = make_provider(
        """
        {
          "company_name": "PayU",
          "event_type": "not_valid",
          "summary": "Test",
          "why_it_matters": "Test",
          "evidence": [],
          "potential_impact": "Test",
          "urgency": "high",
          "confidence": 0.9
        }
        """
    )

    with pytest.raises(
        ValueError,
        match="schema validation",
    ):
        await triage_article(
            AsyncMock(),
            article_id=8,
            company_id=1,
            provider=provider,
        )


@pytest.mark.asyncio
async def test_triage_article_wrong_company(
    monkeypatch,
):
    patch_common(monkeypatch)

    provider = make_provider(
        """
        {
          "company_name": "OtherCompany",
          "event_type": "regulatory_action",
          "summary": "PayU received final RBI approval.",
          "why_it_matters": "The approval supports regulated operations.",
          "evidence": [
            "RBI granted final approval."
          ],
          "potential_impact": "PayU can expand regulated payment services.",
          "urgency": "high",
          "confidence": 0.9
        }
        """
    )

    with pytest.raises(
        ValueError,
        match="unexpected company name",
    ):
        await triage_article(
            AsyncMock(),
            article_id=8,
            company_id=1,
            provider=provider,
        )


@pytest.mark.asyncio
async def test_triage_article_rejects_invalid_rag_limit():
    with pytest.raises(
        ValueError,
        match="RAG retrieval limit must be at least 1",
    ):
        await triage_article(
            AsyncMock(),
            article_id=8,
            company_id=1,
            rag_limit=0,
            provider=make_provider("{}"),
        )

@pytest.mark.asyncio
async def test_triage_article_rejects_ungrounded_evidence(
    monkeypatch,
):
    patch_common(monkeypatch)

    provider = make_provider(
        """
        {
          "company_name": "PayU",
          "event_type": "regulatory_action",
          "summary": "PayU received final RBI approval.",
          "why_it_matters": "The approval supports regulated operations.",
          "evidence": [
            "The company acquired a European bank."
          ],
          "potential_impact": "PayU can expand regulated payment services.",
          "urgency": "high",
          "confidence": 0.9
        }
        """
    )

    save_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.article_triage_service."
        "save_article_triage",
        save_mock,
    )

    with pytest.raises(
        ValueError,
        match="not sufficiently grounded",
    ):
        await triage_article(
            AsyncMock(),
            article_id=8,
            company_id=1,
            provider=provider,
        )

    save_mock.assert_not_awaited()
