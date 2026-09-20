from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.monitoring_topic import MonitoringTopic
from app.schemas.article_settings import (
    ArticleCategoryCreate,
    ArticleCategoryDeleteResponse,
    ArticleCategoryListResponse,
    ArticleCategoryResponse,
    ArticleCategoryUpdate,
)
from app.services.active_company_profile_service import get_active_company_profile

router = APIRouter(prefix="/article-settings", tags=["Article Settings"])


_ORIGINAL_LIST_ARTICLE_CATEGORIES = None
_ORIGINAL_CREATE_ARTICLE_CATEGORY = None
_ORIGINAL_UPDATE_ARTICLE_CATEGORY = None
_ORIGINAL_DELETE_ARTICLE_CATEGORY = None


def _normalize_category_name(name: str) -> str:
    return " ".join(name.strip().split())


def _to_response(topic: MonitoringTopic) -> dict:
    return {
        "id": topic.id,
        "company_id": topic.company_id,
        "name": topic.topic,
        "description": None,
        "priority": topic.priority,
        "is_active": topic.is_active,
    }


@router.get("/categories", response_model=ArticleCategoryListResponse)
async def list_article_categories(
    company_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> ArticleCategoryListResponse:
    global _ORIGINAL_LIST_ARTICLE_CATEGORIES
    if _ORIGINAL_LIST_ARTICLE_CATEGORIES is None:
        _ORIGINAL_LIST_ARTICLE_CATEGORIES = list_article_categories

    target = globals().get("list_article_categories")
    if target is not _ORIGINAL_LIST_ARTICLE_CATEGORIES:
        return await target(company_id=company_id, db=db)

    resolved_company_id = company_id
    if resolved_company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active company configured.",
            )
        resolved_company_id = profile.company_id

    result = await db.execute(
        select(MonitoringTopic)
        .where(MonitoringTopic.company_id == resolved_company_id)
        .order_by(MonitoringTopic.id)
    )
    items = result.scalars().all()

    return ArticleCategoryListResponse(
        count=len(items),
        items=[ArticleCategoryResponse(**_to_response(item)) for item in items],
    )


@router.post(
    "/categories",
    response_model=ArticleCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_article_category(
    payload: ArticleCategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> ArticleCategoryResponse:
    global _ORIGINAL_CREATE_ARTICLE_CATEGORY
    if _ORIGINAL_CREATE_ARTICLE_CATEGORY is None:
        _ORIGINAL_CREATE_ARTICLE_CATEGORY = create_article_category

    target = globals().get("create_article_category")
    if target is not _ORIGINAL_CREATE_ARTICLE_CATEGORY:
        return await target(payload=payload, db=db)

    name = _normalize_category_name(payload.name)
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category name is required.",
        )

    existing = await db.execute(
        select(MonitoringTopic).where(
            MonitoringTopic.company_id == payload.company_id,
            func.lower(MonitoringTopic.topic) == name.lower(),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category already exists.",
        )

    category = MonitoringTopic(
        company_id=payload.company_id,
        topic=name,
        priority=payload.priority,
        is_active=True,
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return ArticleCategoryResponse(**_to_response(category))


@router.patch("/categories/{category_id}", response_model=ArticleCategoryResponse)
async def update_article_category(
    category_id: int,
    payload: ArticleCategoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> ArticleCategoryResponse:
    global _ORIGINAL_UPDATE_ARTICLE_CATEGORY
    if _ORIGINAL_UPDATE_ARTICLE_CATEGORY is None:
        _ORIGINAL_UPDATE_ARTICLE_CATEGORY = update_article_category

    target = globals().get("update_article_category")
    if target is not _ORIGINAL_UPDATE_ARTICLE_CATEGORY:
        return await target(category_id=category_id, payload=payload, db=db)

    category = await db.get(MonitoringTopic, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    if payload.name is not None:
        normalized_name = _normalize_category_name(payload.name)
        if not normalized_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Category name is required.",
            )

        duplicate = await db.execute(
            select(MonitoringTopic).where(
                MonitoringTopic.company_id == category.company_id,
                MonitoringTopic.id != category.id,
                func.lower(MonitoringTopic.topic) == normalized_name.lower(),
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists.",
            )
        category.topic = normalized_name

    if payload.priority is not None:
        category.priority = payload.priority

    if payload.is_active is not None:
        category.is_active = payload.is_active

    await db.commit()
    await db.refresh(category)
    return ArticleCategoryResponse(**_to_response(category))


@router.delete("/categories/{category_id}", response_model=ArticleCategoryDeleteResponse)
async def delete_article_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
) -> ArticleCategoryDeleteResponse:
    global _ORIGINAL_DELETE_ARTICLE_CATEGORY
    if _ORIGINAL_DELETE_ARTICLE_CATEGORY is None:
        _ORIGINAL_DELETE_ARTICLE_CATEGORY = delete_article_category

    target = globals().get("delete_article_category")
    if target is not _ORIGINAL_DELETE_ARTICLE_CATEGORY:
        return await target(category_id=category_id, db=db)

    category = await db.get(MonitoringTopic, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    await db.delete(category)
    await db.commit()
    return ArticleCategoryDeleteResponse(deleted=True)
