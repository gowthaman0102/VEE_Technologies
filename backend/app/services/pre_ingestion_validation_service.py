from dataclasses import dataclass
from datetime import datetime, timezone

from app.ingestion.filters import (
    filter_recent_articles,
)
from app.ingestion.types import CollectedArticle
from app.processing.extractor import ArticleExtractor
from app.processing.url_resolver import (
    resolve_article_url,
)
from app.services.active_company_profile_service import (
    ActiveCompanyProfile,
)
from app.services.article_relevance_gate import (
    contains_company_alias,
)


@dataclass(frozen=True)
class PreIngestionValidationResult:
    accepted: bool
    reason: str
    resolved_url: str
    extracted_content: str | None


async def validate_article_for_company(
    article: CollectedArticle,
    profile: ActiveCompanyProfile,
    *,
    max_age_days: int = 30,
    extractor: ArticleExtractor | None = None,
) -> PreIngestionValidationResult:
    recent = filter_recent_articles(
        [article],
        max_age_days=max_age_days,
        now=datetime.now(timezone.utc),
    )

    if not recent:
        return PreIngestionValidationResult(
            accepted=False,
            reason="stale",
            resolved_url=article.url,
            extracted_content=None,
        )

    resolved_url = resolve_article_url(
        article.url
    )

    article_extractor = (
        extractor
        if extractor is not None
        else ArticleExtractor()
    )

    extraction = (
        await article_extractor.extract_from_url(
            resolved_url
        )
    )

    content = (
        extraction.content
        if extraction.success
        else None
    )

    relevant = contains_company_alias(
        aliases=profile.aliases,
        title=article.title,
        description=article.description,
        content=content,
    )

    if not relevant:
        return PreIngestionValidationResult(
            accepted=False,
            reason="not_relevant",
            resolved_url=resolved_url,
            extracted_content=content,
        )

    return PreIngestionValidationResult(
        accepted=True,
        reason="accepted",
        resolved_url=resolved_url,
        extracted_content=content,
    )

