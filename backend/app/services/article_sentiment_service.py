import json
from dataclasses import dataclass

from app.llm import (
    LLMProvider,
    get_llm_provider,
)
from app.schemas.article_sentiment import (
    ArticleSentimentInference,
    ArticleSentimentResult,
)
from app.services.article_service import (
    get_article,
)
from app.services.article_sentiment_persistence_service import (
    upsert_article_sentiment,
)
from app.services.article_sentiment_prompt_service import (
    build_article_sentiment_prompt,
)
from app.services.company_semantic_context_service import (
    build_company_semantic_context,
)


class SentimentArticleNotFoundError(
    ValueError
):
    pass


class SentimentCompanyNotFoundError(
    ValueError
):
    pass


@dataclass
class ArticleSentimentServiceResult:
    article_id: int
    company_id: int
    sentiment: ArticleSentimentResult


async def analyze_article_sentiment(
    db,
    *,
    article_id: int,
    company_id: int,
    provider: LLMProvider | None = None,
) -> ArticleSentimentServiceResult:
    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        raise SentimentArticleNotFoundError(
            f"Article {article_id} not found."
        )

    company_context = (
        await build_company_semantic_context(
            db,
            company_id,
        )
    )

    if company_context is None:
        raise SentimentCompanyNotFoundError(
            f"Company {company_id} not found."
        )

    prompt = build_article_sentiment_prompt(
        article,
        company_context,
    )

    llm_provider = (
        provider
        if provider is not None
        else get_llm_provider()
    )

    llm_result = await llm_provider.generate(
        prompt,
        response_format=(
            ArticleSentimentInference
            .model_json_schema()
        ),
    )

    try:
        parsed = json.loads(
            llm_result.text
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM returned invalid sentiment JSON."
        ) from exc

    try:
        inference = (
            ArticleSentimentInference
            .model_validate(parsed)
        )
    except Exception as exc:
        raise ValueError(
            "LLM response failed sentiment "
            "schema validation."
        ) from exc

    sentiment = ArticleSentimentResult(
        label=inference.label,
        score=inference.score,
        reason=inference.reason,
        model=llm_result.model,
    )

    await upsert_article_sentiment(
        db,
        article_id=article.id,
        company_id=company_id,
        result=sentiment,
    )

    return ArticleSentimentServiceResult(
        article_id=article.id,
        company_id=company_id,
        sentiment=sentiment,
    )
