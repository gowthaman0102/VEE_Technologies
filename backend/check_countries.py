import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check():
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT publisher_country_name, COUNT(*) 
            FROM articles 
            GROUP BY publisher_country_name
            ORDER BY count DESC
        """))
        total = 0
        unknown = 0
        countries = {}
        for row in res:
            name, count = row[0], row[1]
            total += count
            if name == "Unknown" or not name:
                unknown += count
            else:
                countries[name] = count
            print(f"{name}: {count}")
        print(f"Total: {total}")
        print(f"Unknown: {unknown}")

asyncio.run(check())
