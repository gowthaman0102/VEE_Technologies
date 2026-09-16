import json
from unittest.mock import AsyncMock

import pytest

from app.llm.base import LLMResult
from app.models.article import Article
from app.services.article_business_impact_service import (
    BusinessImpactArticleNotFoundError,
    BusinessImpactCompanyNotFoundError,
    analyze_article_business_impact,
)
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)


def make_article() -> Article:
    return Article(
        id=801,
        source_name="Test Source",
        source_type="rss",
        title="Vee Technologies expands into a new market",
        url="https://example.com/business-impact",
        cleaned_content=(
            "Vee Technologies announced expansion into "
            "a new market and opened additional delivery "
            "capacity to support growing customer demand."
        ),
        extraction_status="success",
        embedding_status="pending",
    )


def make_company_context() -> CompanySemanticContext:
    return CompanySemanticContext(
        company_id=2,
        company_name="VEE Technologies",
        text=(
            "Company: VEE Technologies\n"
            "Industry: Technology and Professional Services"
        ),
    )


class FakeProvider:
    def __init__(self, payload):
        self.payload = payload

    async def generate(
        self,
        prompt,
        *,
        response_format=None,
    ):
        return LLMResult(
            text=json.dumps(self.payload),
            model="fake-model",
        )


@pytest.mark.asyncio
async def test_valid_business_impact(
    monkeypatch,
):
    article = make_article()
    context = make_company_context()

    monkeypatch.setattr(
        "app.services.article_business_impact_service.get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_business_impact_service."
        "build_company_semantic_context",
        AsyncMock(return_value=context),
    )

    persist_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.article_business_impact_service."
        "upsert_article_business_impact",
        persist_mock,
    )

    provider = FakeProvider(
        {
            "primary_category": "market",
            "categories": [
                "market",
                "operational",
                "customer",
            ],
            "impact_summary": (
                "The expansion increases market presence "
                "and operational capacity."
            ),
            "evidence": [
                "The company announced expansion "
                "into a new market.",
                "Additional delivery capacity was opened.",
            ],
        }
    )

    result = await analyze_article_business_impact(
        db=None,
        article_id=801,
        company_id=2,
        provider=provider,
    )

    assert result.article_id == 801
    assert result.company_id == 2

    assert (
        result.impact.primary_category
        == "market"
    )

    assert result.impact.categories == [
        "market",
        "operational",
        "customer",
    ]

    assert result.impact.model == "fake-model"

    persist_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_json_is_rejected(
    monkeypatch,
):
    article = make_article()
    context = make_company_context()

    monkeypatch.setattr(
        "app.services.article_business_impact_service.get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_business_impact_service."
        "build_company_semantic_context",
        AsyncMock(return_value=context),
    )

    class InvalidProvider:
        async def generate(
            self,
            prompt,
            *,
            response_format=None,
        ):
            return LLMResult(
                text="not-json",
                model="fake-model",
            )

    with pytest.raises(
        ValueError,
        match="invalid business impact JSON",
    ):
        await analyze_article_business_impact(
            db=None,
            article_id=801,
            company_id=2,
            provider=InvalidProvider(),
        )


@pytest.mark.asyncio
async def test_primary_category_must_be_in_categories(
    monkeypatch,
):
    article = make_article()
    context = make_company_context()

    monkeypatch.setattr(
        "app.services.article_business_impact_service.get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_business_impact_service."
        "build_company_semantic_context",
        AsyncMock(return_value=context),
    )

    provider = FakeProvider(
        {
            "primary_category": "financial",
            "categories": [
                "market",
            ],
            "impact_summary": (
                "Test impact summary."
            ),
            "evidence": [
                "Test evidence."
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="must also appear in categories",
    ):
        await analyze_article_business_impact(
            db=None,
            article_id=801,
            company_id=2,
            provider=provider,
        )


@pytest.mark.asyncio
async def test_missing_article(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.article_business_impact_service.get_article",
        AsyncMock(return_value=None),
    )

    with pytest.raises(
        BusinessImpactArticleNotFoundError,
    ):
        await analyze_article_business_impact(
            db=None,
            article_id=999,
            company_id=2,
            provider=FakeProvider({}),
        )


@pytest.mark.asyncio
async def test_missing_company(
    monkeypatch,
):
    article = make_article()

    monkeypatch.setattr(
        "app.services.article_business_impact_service.get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_business_impact_service."
        "build_company_semantic_context",
        AsyncMock(return_value=None),
    )

    with pytest.raises(
        BusinessImpactCompanyNotFoundError,
    ):
        await analyze_article_business_impact(
            db=None,
            article_id=801,
            company_id=999,
            provider=FakeProvider({}),
        )
