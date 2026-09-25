from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlsplit

from app.ingestion.types import CollectedArticle
from app.models.article import Article
from app.schemas.article import ArticleCreate
from app.utils.publisher_country_resolver import resolve_publisher_country


async def create_article(
    db: AsyncSession,
    data: ArticleCreate,
) -> Article:
    article = Article(**data.model_dump())

    db.add(article)
    await db.commit()
    await db.refresh(article)

    return article


async def find_existing_article(
    db: AsyncSession,
    source_name: str,
    external_id: str | None,
) -> Article | None:
    if not external_id:
        return None

    result = await db.execute(
        select(Article).where(
            Article.source_name == source_name,
            Article.external_id == external_id,
        )
    )

    return result.scalar_one_or_none()


async def save_collected_article(
    db: AsyncSession,
    data: CollectedArticle,
    *,
    company_id: int | None = None,
) -> tuple[Article, bool]:
    existing = await find_existing_article(
        db,
        source_name=data.source_name,
        external_id=data.external_id,
    )

    if existing is not None:
        return existing, False
        
    try:
        domain = urlsplit(data.url).hostname or ""
    except ValueError:
        domain = ""
        
    country_res = resolve_publisher_country(
        publisher_name=data.source_name,
        publisher_domain=domain,
        canonical_url=data.canonical_url,
    )
    
    data.publisher_country_code = country_res.country_code
    data.publisher_country_name = country_res.country_name
    data.publisher_country_method = country_res.method

    article_data = ArticleCreate(
        company_id=company_id,
        **data.model_dump()
    )

    try:
        article = await create_article(
            db,
            article_data,
        )

        return article, True

    except IntegrityError:
        await db.rollback()

        if data.external_id is None:
            raise

        existing = await find_existing_article(
            db,
            source_name=data.source_name,
            external_id=data.external_id,
        )

        if existing is None:
            raise

        return existing, False


async def get_article(
    db: AsyncSession,
    article_id: int,
) -> Article | None:
    result = await db.execute(
        select(Article).where(
            Article.id == article_id
        )
    )

    return result.scalar_one_or_none()


async def list_articles(
    db: AsyncSession,
    limit: int = 100,
) -> list[Article]:
    result = await db.execute(
        select(Article)
        .order_by(
            Article.collected_at.desc(),
            Article.id.desc(),
        )
        .limit(limit)
    )

    return list(result.scalars().all())
