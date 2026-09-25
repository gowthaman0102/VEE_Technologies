from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.collectors.base import BaseCollector
from app.ingestion.types import CollectedArticle
from app.services.active_company_profile_service import (
    ActiveCompanyProfile,
    get_active_company_profile,
)
from app.services.article_service import save_collected_article
from app.services.pre_ingestion_validation_service import (
    PreIngestionValidationResult,
    validate_article_for_company,
)


ArticleValidator = Callable[
    [
        CollectedArticle,
        ActiveCompanyProfile,
    ],
    Awaitable[
        PreIngestionValidationResult
    ],
]


@dataclass
class IngestionResult:
    collected: int
    inserted: int
    skipped: int
    inserted_article_ids: list[int] = field(
        default_factory=list
    )


async def run_collector(
    db: AsyncSession,
    collector: BaseCollector,
    limit: int | None = None,
    *,
    validator: ArticleValidator | None = None,
    max_age_days: int = 30,
) -> IngestionResult:
    articles = await collector.collect()

    if limit is not None:
        articles = articles[:limit]

    profile = await get_active_company_profile(
        db
    )

    if profile is None:
        raise RuntimeError(
            "No active company configured"
        )

    resolved_validator = (
        validator
        if validator is not None
        else validate_article_for_company
    )

    inserted = 0
    skipped = 0
    inserted_article_ids: list[int] = []

    for article in articles:
        try:
            validation = await resolved_validator(
                article,
                profile,
                max_age_days=max_age_days,
            )
        except TypeError:
            validation = await resolved_validator(
                article,
                profile,
            )

        if not validation.accepted:
            skipped += 1
            continue

        saved_article, created = (
            await save_collected_article(
                db,
                article,
                company_id=profile.company_id,
            )
        )

        if created:
            inserted += 1
            inserted_article_ids.append(
                saved_article.id
            )
        else:
            skipped += 1

    return IngestionResult(
        collected=len(articles),
        inserted=inserted,
        skipped=skipped,
        inserted_article_ids=(
            inserted_article_ids
        ),
    )
