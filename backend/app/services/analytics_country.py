
async def get_publisher_country_distribution(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)
    stmt = (
        select(
            Article.publisher_country_code,
            Article.publisher_country_name,
            func.count(Article.id).label("article_count")
        )
        .join(ArticleTriage, ArticleTriage.article_id == Article.id)
        .where(
            ArticleTriage.company_id == company_id,
            Article.published_at >= start,
            Article.published_at <= end,
        )
        .group_by(Article.publisher_country_code, Article.publisher_country_name)
        .order_by(func.count(Article.id).desc())
    )
    rows = (await db.execute(stmt)).all()
    
    return {
        "distribution": [
            {
                "country_code": row.publisher_country_code,
                "country_name": row.publisher_country_name if row.publisher_country_name else "Unknown",
                "article_count": row.article_count
            }
            for row in rows
        ]
    }
