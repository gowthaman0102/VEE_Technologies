"""Backfill deterministic publisher-country metadata for stored articles."""

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.article import Article
from app.utils.publisher_country import resolve_publisher_country


async def backfill() -> int:
    updated = 0
    async with AsyncSessionLocal() as db:
        articles = (await db.scalars(select(Article))).yield_per(200)
        for article in articles:
            result = resolve_publisher_country(
                article.source_name,
                article.title,
                article.url,
                article.canonical_url,
            )
            if (
                article.publisher_country_code != result.country_code
                or article.publisher_country != result.country_name
                or article.publisher_country_resolution != result.resolution_method
            ):
                article.publisher_country_code = result.country_code
                article.publisher_country = result.country_name
                article.publisher_country_resolution = result.resolution_method
                updated += 1
                if updated % 200 == 0:
                    await db.commit()
        await db.commit()
    return updated


if __name__ == "__main__":
    print(f"Updated {asyncio.run(backfill())} articles")
