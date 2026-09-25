import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def check_articles():
    engine = create_async_engine('postgresql+asyncpg://media_user:VeeMediaDev_2026@localhost:5432/media_intelligence')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id, url, source_name FROM articles WHERE url LIKE '%pcmagcom.com%' OR url LIKE '%dwenglish.com%'"))
        print(res.fetchall())
asyncio.run(check_articles())
