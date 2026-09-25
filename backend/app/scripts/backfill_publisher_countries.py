import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.article import Article
from app.utils.publisher_country_resolver import resolve_publisher_country
from urllib.parse import urlsplit

async def backfill():
    async with AsyncSessionLocal() as db:
        # Get unresolved articles
        query = select(Article).where(
            (Article.publisher_country_name == None) |
            (Article.publisher_country_name == '') |
            (Article.publisher_country_name == 'Unknown') |
            (Article.publisher_country_name == 'unresolved')
        )
        result = await db.execute(query)
        articles = result.scalars().all()
        
        unique_publishers = set()
        resolved_publishers = set()
        unresolved_publishers = set()
        updated_count = 0
        
        # Cache resolution
        publisher_resolution_cache = {}
        
        for article in articles:
            unique_publishers.add(article.source_name)
            
            try:
                domain = urlsplit(article.url).hostname or ""
            except ValueError:
                domain = ""
                
            cache_key = (article.source_name, domain, article.canonical_url)
            
            if cache_key not in publisher_resolution_cache:
                res = resolve_publisher_country(
                    publisher_name=article.source_name,
                    publisher_domain=domain,
                    canonical_url=article.canonical_url
                )
                publisher_resolution_cache[cache_key] = res
            else:
                res = publisher_resolution_cache[cache_key]
            
            article.publisher_country_code = res.country_code
            article.publisher_country_name = res.country_name
            article.publisher_country_method = res.method
            
            if res.method == "unknown":
                unresolved_publishers.add(article.source_name)
            else:
                resolved_publishers.add(article.source_name)
                
            updated_count += 1
            
        await db.commit()
        
        print("NOVA COPS PUBLISHER COUNTRY CLASSIFICATION")
        print("BACKFILL REPORT")
        print("------------------------------------------")
        print(f"Total unique publishers: {len(unique_publishers)}")
        print(f"Resolved publishers: {len(resolved_publishers)}")
        print(f"Unknown publishers: {len(unresolved_publishers)}")
        print(f"Articles updated: {updated_count}")
        print(f"Articles unresolved: {len([a for a in articles if a.publisher_country_method == 'unknown'])}")
        print("------------------------------------------")
        if unresolved_publishers:
            print("Unresolved publisher names:")
            for p in sorted(list(unresolved_publishers)):
                print(f"- {p}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(backfill())
