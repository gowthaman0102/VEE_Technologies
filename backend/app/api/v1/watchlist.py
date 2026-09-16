from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.watchlist import (
    WatchlistDeleteResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
    WatchlistListResponse,
)
from app.services.watchlist_service import (
    create_watchlist_item,
    delete_watchlist_item,
    list_watchlist_items,
    update_watchlist_item,
)

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("", response_model=WatchlistListResponse)
async def read_watchlist(
    company_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> WatchlistListResponse:
    data = await list_watchlist_items(db, company_id=company_id)
    return WatchlistListResponse(
        count=data["count"],
        items=[
            WatchlistItemResponse(**item)
            for item in data["items"]
        ],
    )


@router.post(
    "",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_watchlist_entry(
    payload: WatchlistItemCreate,
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemResponse:
    data = await create_watchlist_item(
        db,
        company_id=payload.company_id,
        item_type=payload.item_type,
        item_name=payload.item_name,
        value=payload.value,
    )
    return WatchlistItemResponse(**data)


@router.delete("/{item_id}", response_model=WatchlistDeleteResponse)
async def delete_watchlist_entry(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> WatchlistDeleteResponse:
    deleted = await delete_watchlist_item(db, item_id=item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found.",
        )
    return WatchlistDeleteResponse(deleted=True)


@router.patch("/{item_id}", response_model=WatchlistItemResponse)
async def update_watchlist_entry(
    item_id: int,
    payload: WatchlistItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemResponse:
    data = await update_watchlist_item(
        db,
        item_id=item_id,
        values=payload.model_dump(exclude_unset=True),
    )
    if data is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found.")
    return WatchlistItemResponse(**data)
