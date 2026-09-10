import json
from dataclasses import dataclass

from app.llm import LLMProvider, get_llm_provider
from app.schemas.article_triage import ArticleTriageResult
from app.services.article_service import get_article
from app.services.article_triage_grounding_service import (
    validate_triage_grounding,
)
from app.services.article_triage_persistence_service import (
    save_article_triage,
)
from app.services.article_triage_prompt_service import (
    build_article_triage_prompt,
)
from app.services.company_semantic_context_service import (
    build_company_semantic_context,
)
from app.services.rag_context_service import (
    retrieve_rag_context,
)


class ArticleNotFoundError(ValueError):
    pass


class CompanyNotFoundError(ValueError):
    pass


@dataclass
class ArticleTriageServiceResult:
    article_id: int
    model: str
    triage: ArticleTriageResult


async def triage_article(
    db,
    article_id: int,
    company_id: int,
    *,
    provider: LLMProvider | None = None,
    rag_limit: int = 3,
) -> ArticleTriageServiceResult:
    if rag_limit < 1:
        raise ValueError(
            "RAG retrieval limit must be at least 1."
        )

    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        raise ArticleNotFoundError(
            f"Article {article_id} not found."
        )

    company_context = await build_company_semantic_context(
        db,
        company_id,
    )

    if company_context is None:
        raise CompanyNotFoundError(
            f"Company {company_id} not found."
        )

    rag_context = await retrieve_rag_context(
        db,
        article,
        company_name=company_context.company_name,
        limit=rag_limit,
    )

    prompt = build_article_triage_prompt(
        article,
        company_context,
        rag_context,
    )

    llm_provider = (
        provider
        if provider is not None
        else get_llm_provider()
    )

    result = await llm_provider.generate(
        prompt,
        response_format=(
            ArticleTriageResult.model_json_schema()
        ),
    )

    try:
        parsed = json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM returned invalid JSON."
        ) from exc

    try:
        triage = ArticleTriageResult.model_validate(
            parsed
        )
    except Exception as exc:
        raise ValueError(
            "LLM response failed triage schema validation."
        ) from exc

    if triage.company_name != company_context.company_name:
        raise ValueError(
            "LLM returned an unexpected company name."
        )

    validate_triage_grounding(
        article_content=article.cleaned_content or "",
        triage=triage,
    )

    await save_article_triage(
        db,
        article_id=article.id,
        company_id=company_id,
        model=result.model,
        triage=triage,
    )

    return ArticleTriageServiceResult(
        article_id=article.id,
        model=result.model,
        triage=triage,
    )
