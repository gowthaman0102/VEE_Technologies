import json
from unittest.mock import AsyncMock

import pytest

from app.llm.base import LLMResult
from app.models.article import Article
from app.services.article_sentiment_service import (
    SentimentArticleNotFoundError,
    SentimentCompanyNotFoundError,
    analyze_article_sentiment,
)
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)


def make_article() -> Article:
    return Article(
        id=101,
        source_name="Test Source",
        source_type="rss",
        title="Vee Technologies expands operations",
        url="https://example.com/article",
        cleaned_content=(
            "Vee Technologies announced a new facility "
            "and plans to expand its operations."
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
@pytest.mark.parametrize(
    "label,score",
    [
        ("positive", 0.94),
        ("neutral", 0.72),
        ("negative", 0.89),
    ],
)
async def test_sentiment_labels(
    monkeypatch,
    label,
    score,
):
    article = make_article()
    company_context = make_company_context()

    monkeypatch.setattr(
        "app.services.article_sentiment_service.get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_sentiment_service."
        "build_company_semantic_context",
        AsyncMock(return_value=company_context),
    )

    persist_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.article_sentiment_service."
        "upsert_article_sentiment",
        persist_mock,
    )

    provider = FakeProvider(
        {
            "label": label,
            "score": score,
            "reason": "Grounded sentiment reason.",
        }
    )

    result = await analyze_article_sentiment(
        db=None,
        article_id=101,
        company_id=2,
        provider=provider,
    )

    assert result.article_id == 101
    assert result.company_id == 2
    assert result.sentiment.label == label
    assert result.sentiment.score == score
    assert result.sentiment.reason == (
        "Grounded sentiment reason."
    )
    assert result.sentiment.model == "fake-model"

    persist_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_json_is_rejected(
    monkeypatch,
):
    article = make_article()
    company_context = make_company_context()

    monkeypatch.setattr(
        "app.services.article_sentiment_service.get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_sentiment_service."
        "build_company_semantic_context",
        AsyncMock(return_value=company_context),
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
        match="invalid sentiment JSON",
    ):
        await analyze_article_sentiment(
            db=None,
            article_id=101,
            company_id=2,
            provider=InvalidProvider(),
        )


@pytest.mark.asyncio
async def test_missing_article(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.article_sentiment_service.get_article",
        AsyncMock(return_value=None),
    )

    with pytest.raises(
        SentimentArticleNotFoundError,
    ):
        await analyze_article_sentiment(
            db=None,
            article_id=999,
            company_id=2,
            provider=FakeProvider(
                {
                    "label": "neutral",
                    "score": 0.5,
                    "reason": "Test",
                }
            ),
        )


@pytest.mark.asyncio
async def test_missing_company(
    monkeypatch,
):
    article = make_article()

    monkeypatch.setattr(
        "app.services.article_sentiment_service.get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        "app.services.article_sentiment_service."
        "build_company_semantic_context",
        AsyncMock(return_value=None),
    )

    with pytest.raises(
        SentimentCompanyNotFoundError,
    ):
        await analyze_article_sentiment(
            db=None,
            article_id=101,
            company_id=999,
            provider=FakeProvider(
                {
                    "label": "neutral",
                    "score": 0.5,
                    "reason": "Test",
                }
            ),
        )
