import argparse
import asyncio

from app.db.celery_session import CeleryAsyncSessionLocal
from app.services.article_recovery_service import (
    queue_incomplete_active_articles,
)


async def main(limit: int | None) -> None:
    async with CeleryAsyncSessionLocal() as db:
        result = await queue_incomplete_active_articles(
            db,
            limit=limit,
        )
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    asyncio.run(main(args.limit))