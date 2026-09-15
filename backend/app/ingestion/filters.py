from datetime import datetime, timedelta, timezone

from app.ingestion.types import CollectedArticle


def filter_recent_articles(
    articles: list[CollectedArticle],
    max_age_days: int,
    now: datetime | None = None,
) -> list[CollectedArticle]:
    if max_age_days <= 0:
        raise ValueError(
            "max_age_days must be greater than zero"
        )

    current_time = (
        now
        if now is not None
        else datetime.now(timezone.utc)
    )

    if current_time.tzinfo is None:
        current_time = current_time.replace(
            tzinfo=timezone.utc
        )

    cutoff = current_time - timedelta(
        days=max_age_days
    )

    recent: list[CollectedArticle] = []

    for article in articles:
        published_at = article.published_at

        if published_at is None:
            recent.append(article)
            continue

        if published_at.tzinfo is None:
            published_at = published_at.replace(
                tzinfo=timezone.utc
            )

        if published_at >= cutoff:
            recent.append(article)

    return recent
