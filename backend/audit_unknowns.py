import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.article import Article
from urllib.parse import urlparse

async def main():
    async with AsyncSessionLocal() as session:
        query = select(
            Article.id,
            Article.source_name,
            Article.url,
            Article.title,
            Article.publisher_country_name
        ).where(
            (Article.publisher_country_name == None) |
            (Article.publisher_country_name == '') |
            (Article.publisher_country_name == 'Unknown') |
            (Article.publisher_country_name == 'unresolved')
        )
        
        result = await session.execute(query)
        articles = result.all()
        
        print(f"Total unknown articles: {len(articles)}")
        
        publishers = {}
        for a in articles:
            # Extract domain
            try:
                domain = urlparse(a.url).netloc
            except:
                domain = "unknown_domain"
                
            key = (a.source_name, domain)
            if key not in publishers:
                publishers[key] = {
                    'count': 0,
                    'sample_id': a.id,
                    'sample_title': a.title,
                    'url': a.url
                }
            publishers[key]['count'] += 1
            
        print("\nUNIQUE UNKNOWN PUBLISHERS:")
        for (source_name, domain), data in sorted(publishers.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"Publisher: {source_name} | Domain: {domain} | Count: {data['count']}")
            print(f"Sample Article - ID: {data['sample_id']}, Title: {data['sample_title']}, URL: {data['url']}")
            print("-" * 50)
            
if __name__ == "__main__":
    asyncio.run(main())
