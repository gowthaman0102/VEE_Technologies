import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def change_pwd():
    engine = create_async_engine('postgresql+asyncpg://media_user:change_me@localhost:5432/media_intelligence')
    async with engine.begin() as conn:
        await conn.execute(text("ALTER USER media_user WITH PASSWORD 'VeeMediaDev_2026';"))
        print('Password updated')
asyncio.run(change_pwd())
