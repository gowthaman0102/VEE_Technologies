from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.watchlist import (
    WatchlistDeleteResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
    WatchlistListResponse,
    WatchlistMatchListResponse,
    WatchlistMatchResponse,
)
from app.services.watchlist_service import (
    create_watchlist_item,
    delete_watchlist_item,
    list_watchlist_items,
    update_watchlist_item,
)
from app.services.watchlist_matching_service import (
    match_watchlist_items,
)

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get(
    "/matches",
    response_model=WatchlistMatchListResponse,
)
async def read_watchlist_matches(
    company_id: int = Query(ge=1),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> WatchlistMatchListResponse:
    if (
        start is not None
        and end is not None
        and start >= end
    ):
        raise HTTPException(
            status_code=422,
            detail="start must be earlier than end.",
        )

    matches = await match_watchlist_items(
        db,
        company_id=company_id,
        start=start,
        end=end,
        limit=limit,
    )

    return WatchlistMatchListResponse(
        count=len(matches),
        matches=[
            WatchlistMatchResponse(
                watchlist_item_id=item.watchlist_item_id,
                item_type=item.item_type,
                item_name=item.item_name,
                value=item.value,
                article_id=item.article_id,
                title=item.title,
                publisher_name=item.publisher_name,
                source_name=item.source_name,
                url=item.url,
                published_at=(
                    item.published_at.isoformat()
                    if item.published_at is not None
                    else None
                ),
                collected_at=item.collected_at.isoformat(),
                event_type=item.event_type,
                monitoring_topic=item.monitoring_topic,
                risk_level=item.risk_level,
                risk_score=item.risk_score,
                business_impact=item.business_impact,
            )
            for item in matches
        ],
    )


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
