from dataclasses import dataclass, field

from app.llm import LLMProvider
from app.services.article_triage_service import (
    ArticleNotFoundError,
    ArticleTriageServiceResult,
    CompanyNotFoundError,
    triage_article,
)


@dataclass
class ArticleTriageBatchItem:
    article_id: int
    status: str
    result: ArticleTriageServiceResult | None = None
    error: str | None = None


@dataclass
class ArticleTriageBatchResult:
    company_id: int
    requested_count: int
    success_count: int
    not_found_count: int
    failed_count: int
    items: list[ArticleTriageBatchItem] = field(
        default_factory=list
    )


async def triage_articles_batch(
    db,
    *,
    article_ids: list[int],
    company_id: int,
    provider: LLMProvider | None = None,
    rag_limit: int = 3,
) -> ArticleTriageBatchResult:
    if not article_ids:
        raise ValueError(
            "At least one article ID is required."
        )

    if company_id < 1:
        raise ValueError(
            "Company ID must be at least 1."
        )

    unique_article_ids = list(
        dict.fromkeys(article_ids)
    )

    items: list[ArticleTriageBatchItem] = []

    success_count = 0
    not_found_count = 0
    failed_count = 0

    for article_id in unique_article_ids:
        try:
            result = await triage_article(
                db,
                article_id=article_id,
                company_id=company_id,
                provider=provider,
                rag_limit=rag_limit,
            )

            success_count += 1

            items.append(
                ArticleTriageBatchItem(
                    article_id=article_id,
                    status="success",
                    result=result,
                )
            )

        except ArticleNotFoundError:
            not_found_count += 1

            items.append(
                ArticleTriageBatchItem(
                    article_id=article_id,
                    status="not_found",
                )
            )

        except CompanyNotFoundError:
            raise

        except Exception as exc:
            failed_count += 1

            items.append(
                ArticleTriageBatchItem(
                    article_id=article_id,
                    status="failed",
                    error=str(exc),
                )
            )

    return ArticleTriageBatchResult(
        company_id=company_id,
        requested_count=len(unique_article_ids),
        success_count=success_count,
        not_found_count=not_found_count,
        failed_count=failed_count,
        items=items,
    )
