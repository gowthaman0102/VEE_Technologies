import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.tasks.ingestion_tasks import _run_live_ingestion

async def test_ingestion():
    result = await _run_live_ingestion()
    print("Ingestion Result:", result)

if __name__ == "__main__":
    asyncio.run(test_ingestion())
