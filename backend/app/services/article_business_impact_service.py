import json
from dataclasses import dataclass

from app.llm import (
    LLMProvider,
    get_llm_provider,
)
from app.schemas.article_business_impact import (
    ArticleBusinessImpactInference,
    ArticleBusinessImpactResult,
)
from app.services.article_business_impact_persistence_service import (
    upsert_article_business_impact,
)
from app.services.article_business_impact_prompt_service import (
    build_article_business_impact_prompt,
)
from app.services.article_service import (
    get_article,
)
from app.services.company_semantic_context_service import (
    build_company_semantic_context,
)


class BusinessImpactArticleNotFoundError(
    ValueError
):
    pass


class BusinessImpactCompanyNotFoundError(
    ValueError
):
    pass


@dataclass
class ArticleBusinessImpactServiceResult:
    article_id: int
    company_id: int
    impact: ArticleBusinessImpactResult


async def analyze_article_business_impact(
    db,
    *,
    article_id: int,
    company_id: int,
    provider: LLMProvider | None = None,
) -> ArticleBusinessImpactServiceResult:
    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        raise BusinessImpactArticleNotFoundError(
            f"Article {article_id} not found."
        )

    company_context = (
        await build_company_semantic_context(
            db,
            company_id,
        )
    )

    if company_context is None:
        raise BusinessImpactCompanyNotFoundError(
            f"Company {company_id} not found."
        )

    prompt = build_article_business_impact_prompt(
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
            ArticleBusinessImpactInference
            .model_json_schema()
        ),
    )

    try:
        parsed = json.loads(
            llm_result.text
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM returned invalid business impact JSON."
        ) from exc

    try:
        inference = (
            ArticleBusinessImpactInference
            .model_validate(parsed)
        )
    except Exception as exc:
        raise ValueError(
            "LLM response failed business impact "
            "schema validation."
        ) from exc

    if (
        inference.primary_category
        not in inference.categories
    ):
        raise ValueError(
            "Primary business impact category must "
            "also appear in categories."
        )

    impact = ArticleBusinessImpactResult(
        primary_category=(
            inference.primary_category
        ),
        categories=inference.categories,
        impact_summary=(
            inference.impact_summary
        ),
        evidence=inference.evidence,
        model=llm_result.model,
    )

    await upsert_article_business_impact(
        db,
        article_id=article.id,
        company_id=company_id,
        result=impact,
    )

    return ArticleBusinessImpactServiceResult(
        article_id=article.id,
        company_id=company_id,
        impact=impact,
    )
