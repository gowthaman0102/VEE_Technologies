from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.schemas.client import ClientCreate


async def create_client(
    db: AsyncSession,
    data: ClientCreate,
) -> Client:
    client = Client(
        name=data.name,
        description=data.description,
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    return client


async def get_client(
    db: AsyncSession,
    client_id: int,
) -> Client | None:
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )

    return result.scalar_one_or_none()


async def list_clients(
    db: AsyncSession,
) -> list[Client]:
    result = await db.execute(
        select(Client).order_by(Client.id)
    )

    return list(result.scalars().all())
