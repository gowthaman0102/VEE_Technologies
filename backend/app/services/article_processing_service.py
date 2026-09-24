from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.processing.extractor import (
    ArticleExtractor,
    ExtractionResult,
)
from app.processing.normalization import (
    canonicalize_url,
    clean_text,
    content_hash,
)
from app.processing.url_resolver import (
    resolve_article_url,
)
from app.services.article_service import get_article
from app.utils.publisher_country import resolve_publisher_country


@dataclass
class ArticleProcessingResult:
    article_id: int
    status: str
    duplicate_of_id: int | None = None
    content_hash: str | None = None
    error: str | None = None


async def find_canonical_duplicate(
    db: AsyncSession,
    article_id: int,
    canonical_url: str,
) -> Article | None:
    if not canonical_url:
        return None

    result = await db.execute(
        select(Article).where(
            Article.id != article_id,
            Article.canonical_url == canonical_url,
        )
    )

    return result.scalars().first()


async def find_content_duplicate(
    db: AsyncSession,
    article_id: int,
    hash_value: str | None,
) -> Article | None:
    if not hash_value:
        return None

    result = await db.execute(
        select(Article).where(
            Article.id != article_id,
            Article.content_hash == hash_value,
        )
    )

    return result.scalars().first()


async def process_article(
    db: AsyncSession,
    article: Article,
    extractor: ArticleExtractor | None = None,
) -> ArticleProcessingResult:
    extractor = extractor or ArticleExtractor()

    resolved_url = resolve_article_url(
        article.url
    )

    initial_canonical_url = canonicalize_url(
        resolved_url
    )

    duplicate = await find_canonical_duplicate(
        db,
        article_id=article.id,
        canonical_url=initial_canonical_url,
    )

    if duplicate is not None:
        article.canonical_url = initial_canonical_url
        article.extraction_status = "skipped"
        article.extraction_error = (
            "Duplicate canonical URL "
            f"of article {duplicate.id}"
        )
        article.processed_at = datetime.now(
            timezone.utc
        )

        await db.commit()
        await db.refresh(article)

        return ArticleProcessingResult(
            article_id=article.id,
            status="skipped",
            duplicate_of_id=duplicate.id,
        )

    if (
        article.source_name == "OpenAI Official News"
        and article.description
        and article.description.strip()
    ):
        extraction = ExtractionResult(
            success=True,
            content=(
                f"{article.title}\n\n"
                f"{article.description.strip()}"
            ),
            error="Used official OpenAI RSS description",
            final_url=resolved_url,
        )
    else:
        extraction = await extractor.extract_from_url(
            resolved_url
        )

    if (
        not extraction.success
        and article.description
        and article.description.strip()
    ):
        extraction = type(extraction)(
            success=True,
            content=(
                f"{article.title}\n\n"
                f"{article.description.strip()}"
            ),
            error=(
                "Article page unavailable; used source-provided "
                "description"
            ),
            final_url=extraction.final_url or resolved_url,
        )

    final_canonical_url = canonicalize_url(
        extraction.final_url
        or resolved_url
    )

    article.canonical_url = final_canonical_url
    country = resolve_publisher_country(
        article.source_name,
        article.title,
        article.url,
        final_canonical_url,
    )
    article.publisher_country_code = country.country_code
    article.publisher_country = country.country_name
    article.publisher_country_resolution = country.resolution_method
    article.processed_at = datetime.now(
        timezone.utc
    )

    if not extraction.success:
        article.extraction_status = "failed"
        article.extraction_error = (
            extraction.error
            or "Article extraction failed"
        )

        await db.commit()
        await db.refresh(article)

        return ArticleProcessingResult(
            article_id=article.id,
            status="failed",
            error=article.extraction_error,
        )

    canonical_duplicate = (
        await find_canonical_duplicate(
            db,
            article_id=article.id,
            canonical_url=final_canonical_url,
        )
    )

    cleaned = clean_text(
        extraction.content
    )

    hash_value = content_hash(
        cleaned
    )

    article.extracted_content = (
        extraction.content
    )
    article.cleaned_content = cleaned
    article.content_hash = hash_value

    if canonical_duplicate is not None:
        article.extraction_status = "skipped"
        article.extraction_error = (
            "Duplicate canonical URL "
            f"of article {canonical_duplicate.id}"
        )

        await db.commit()
        await db.refresh(article)

        return ArticleProcessingResult(
            article_id=article.id,
            status="skipped",
            duplicate_of_id=(
                canonical_duplicate.id
            ),
            content_hash=hash_value,
        )

    content_duplicate = (
        await find_content_duplicate(
            db,
            article_id=article.id,
            hash_value=hash_value,
        )
    )

    if content_duplicate is not None:
        article.extraction_status = "skipped"
        article.extraction_error = (
            "Duplicate content "
            f"of article {content_duplicate.id}"
        )

        await db.commit()
        await db.refresh(article)

        return ArticleProcessingResult(
            article_id=article.id,
            status="skipped",
            duplicate_of_id=(
                content_duplicate.id
            ),
            content_hash=hash_value,
        )

    article.extraction_status = "success"
    article.extraction_error = None

    await db.commit()
    await db.refresh(article)

    return ArticleProcessingResult(
        article_id=article.id,
        status="success",
        content_hash=hash_value,
    )


async def process_article_by_id(
    db: AsyncSession,
    article_id: int,
    extractor: ArticleExtractor | None = None,
) -> ArticleProcessingResult | None:
    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        return None

    return await process_article(
        db,
        article,
        extractor=extractor,
    )
