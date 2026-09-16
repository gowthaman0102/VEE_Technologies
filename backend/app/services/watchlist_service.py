from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import WatchlistItem


async def list_watchlist_items(
    db: AsyncSession,
    *,
    company_id: int | None = None,
) -> dict:
    stmt = select(WatchlistItem)
    if company_id is not None:
        stmt = stmt.where(WatchlistItem.company_id == company_id)
    stmt = stmt.order_by(WatchlistItem.id)

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return {
        "count": len(items),
        "items": [
            {
                "id": item.id,
                "company_id": item.company_id,
                "item_type": item.item_type,
                "item_name": item.item_name,
                "value": item.value,
                "is_active": item.is_active,
            }
            for item in items
        ],
    }


async def create_watchlist_item(
    db: AsyncSession,
    *,
    company_id: int,
    item_type: str,
    item_name: str,
    value: str,
) -> dict:
    item = WatchlistItem(
        company_id=company_id,
        item_type=item_type,
        item_name=item_name,
        value=value,
        is_active=True,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return {
        "id": item.id,
        "company_id": item.company_id,
        "item_type": item.item_type,
        "item_name": item.item_name,
        "value": item.value,
        "is_active": item.is_active,
    }


async def delete_watchlist_item(
    db: AsyncSession,
    *,
    item_id: int,
) -> bool:
    item = await db.get(WatchlistItem, item_id)
    if item is None:
        return False

    await db.delete(item)
    await db.commit()
    return True
