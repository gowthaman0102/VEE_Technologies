import asyncio
from datetime import datetime, timezone
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.article import Article
from app.ingestion.sources import get_enabled_sources

async def test_dedup():
    async with AsyncSessionLocal() as db:
        enabled_source_names = [s.name for s in get_enabled_sources()]
        
        article_time = func.coalesce(Article.published_at, Article.collected_at)
        start_date = datetime(2026, 9, 7, tzinfo=timezone.utc)
        end_date = datetime(2026, 9, 14, tzinfo=timezone.utc)
        snapshot_at = datetime(2026, 9, 19, 10, 43, tzinfo=timezone.utc) # Time when the original PDF was generated (10:43 IST = 05:13 UTC)
        
        stmt = (
            select(Article)
            .where(
                article_time >= start_date,
                article_time < end_date,
                Article.collected_at <= snapshot_at,
                Article.source_name.in_(enabled_source_names)
            )
            .order_by(
                article_time.desc(),
                Article.id.desc(),
            )
        )
        
        articles = list((await db.execute(stmt)).scalars().all())
        
        # Dedup in memory
        seen_ext = set()
        seen_url = set()
        unique_articles = []
        for a in articles:
            # deduplicate
            is_dup = False
            if a.external_id:
                if a.external_id in seen_ext:
                    is_dup = True
                seen_ext.add(a.external_id)
            if a.url:
                if a.url in seen_url:
                    is_dup = True
                seen_url.add(a.url)
                
            if not is_dup:
                unique_articles.append(a)
                
        print(f"Total articles before dedup: {len(articles)}")
        print(f"Total articles after dedup: {len(unique_articles)}")
        
        for a in unique_articles:
            print(a.id, a.source_name, a.title[:50])

asyncio.run(test_dedup())
