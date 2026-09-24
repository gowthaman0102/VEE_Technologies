"""
Backfill sentiment analysis for existing articles.

Usage:
    python -m app.scripts.backfill_sentiment [options]

Options:
    --force           Recompute all articles, even those with existing sentiment.
    --company-id N    Only process articles for a specific company.
    --batch-size N    Number of articles to process per batch (default: 100).
    --dry-run         Log what would be processed without making LLM calls.

Default behaviour (no flags):
    Process only articles that have NO sentiment for the active/specified company.

Examples:
    # Backfill only missing sentiment
    python -m app.scripts.backfill_sentiment

    # Force recompute for a single company
    python -m app.scripts.backfill_sentiment --force --company-id 1

    # Dry run to see scope
    python -m app.scripts.backfill_sentiment --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.celery_session import CeleryAsyncSessionLocal
from app.models.article import Article
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.company import Company
from app.services.article_sentiment_service import (
    SentimentArticleNotFoundError,
    SentimentCompanyNotFoundError,
    analyze_article_sentiment,
)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


async def _get_target_company_ids(
    db: AsyncSession,
    company_id: int | None,
) -> list[int]:
    """Return company IDs to process."""
    if company_id is not None:
        return [company_id]

    result = await db.execute(
        select(Company.id).where(
            Company.is_active.is_(True)
        )
    )
    return list(result.scalars().all())


async def _get_articles_missing_sentiment(
    db: AsyncSession,
    *,
    company_id: int,
) -> list[int]:
    """Article IDs that have a triage but no sentiment for this company."""
    # All triaged article IDs for this company
    triaged_subq = (
        select(ArticleTriage.article_id)
        .where(ArticleTriage.company_id == company_id)
        .scalar_subquery()
    )

    # Article IDs that already have sentiment
    analyzed_subq = (
        select(ArticleSentiment.article_id)
        .where(ArticleSentiment.company_id == company_id)
        .scalar_subquery()
    )

    stmt = (
        select(Article.id)
        .where(
            Article.id.in_(triaged_subq),
            Article.id.not_in(analyzed_subq),
            Article.extraction_status == "success",
        )
        .order_by(Article.id.asc())
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_all_triaged_articles(
    db: AsyncSession,
    *,
    company_id: int,
) -> list[int]:
    """All successfully extracted article IDs triaged for this company."""
    stmt = (
        select(ArticleTriage.article_id)
        .join(Article, Article.id == ArticleTriage.article_id)
        .where(
            ArticleTriage.company_id == company_id,
            Article.extraction_status == "success",
        )
        .order_by(ArticleTriage.article_id.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _chunks(lst: list, size: int):
    """Yield successive chunks from lst."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


async def _backfill_company(
    *,
    company_id: int,
    force: bool,
    batch_size: int,
    dry_run: bool,
) -> dict:
    stats = {
        "company_id": company_id,
        "total": 0,
        "processed": 0,
        "skipped": 0,
        "errors": 0,
    }

    async with CeleryAsyncSessionLocal() as db:
        if force:
            article_ids = await _get_all_triaged_articles(
                db, company_id=company_id
            )
        else:
            article_ids = await _get_articles_missing_sentiment(
                db, company_id=company_id
            )

    stats["total"] = len(article_ids)

    logger.info(
        "Company %d: %d articles to process (force=%s, dry_run=%s)",
        company_id,
        stats["total"],
        force,
        dry_run,
    )

    if dry_run:
        logger.info(
            "Company %d: dry-run complete — no LLM calls made.", company_id
        )
        return stats

    for batch_num, batch in enumerate(
        _chunks(article_ids, batch_size), start=1
    ):
        logger.info(
            "Company %d: batch %d (%d articles)",
            company_id,
            batch_num,
            len(batch),
        )

        for article_id in batch:
            t0 = time.monotonic()

            try:
                async with CeleryAsyncSessionLocal() as db:
                    await analyze_article_sentiment(
                        db,
                        article_id=article_id,
                        company_id=company_id,
                    )

                elapsed = time.monotonic() - t0
                logger.info(
                    "Company %d | article %d → OK (%.2fs)",
                    company_id,
                    article_id,
                    elapsed,
                )
                stats["processed"] += 1

            except SentimentArticleNotFoundError:
                logger.warning(
                    "Company %d | article %d → SKIP: article not found",
                    company_id,
                    article_id,
                )
                stats["skipped"] += 1

            except SentimentCompanyNotFoundError:
                logger.warning(
                    "Company %d | article %d → SKIP: company context not found",
                    company_id,
                    article_id,
                )
                stats["skipped"] += 1

            except ValueError as exc:
                logger.warning(
                    "Company %d | article %d → SKIP: %s",
                    company_id,
                    article_id,
                    exc,
                )
                stats["skipped"] += 1

            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Company %d | article %d → ERROR: %s",
                    company_id,
                    article_id,
                    exc,
                )
                stats["errors"] += 1

    return stats


async def main(
    *,
    company_id: int | None,
    force: bool,
    batch_size: int,
    dry_run: bool,
) -> None:
    async with CeleryAsyncSessionLocal() as db:
        company_ids = await _get_target_company_ids(db, company_id)

    if not company_ids:
        logger.warning("No active companies found. Nothing to process.")
        return

    logger.info(
        "Starting sentiment backfill for companies: %s",
        company_ids,
    )

    overall_stats: list[dict] = []

    for cid in company_ids:
        stats = await _backfill_company(
            company_id=cid,
            force=force,
            batch_size=batch_size,
            dry_run=dry_run,
        )
        overall_stats.append(stats)

    # Summary
    logger.info("=" * 60)
    logger.info("Sentiment backfill complete")
    logger.info("=" * 60)
    for stats in overall_stats:
        logger.info(
            "Company %d: total=%d processed=%d skipped=%d errors=%d",
            stats["company_id"],
            stats["total"],
            stats["processed"],
            stats["skipped"],
            stats["errors"],
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill article sentiment analysis."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute all articles, even those with existing sentiment.",
    )
    parser.add_argument(
        "--company-id",
        type=int,
        default=None,
        metavar="N",
        help="Only process articles for this company ID.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        metavar="N",
        help="Articles per batch (default: 100).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be processed without making LLM calls.",
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            company_id=args.company_id,
            force=args.force,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    )
