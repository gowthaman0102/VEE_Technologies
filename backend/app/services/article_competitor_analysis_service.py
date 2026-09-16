from dataclasses import dataclass

from app.services.article_competitor_mention_persistence_service import (
    upsert_article_competitor_mentions,
)
from app.services.article_service import get_article
from app.services.competitor_mention_service import (
    CompetitorMentionResult,
    detect_competitor_mentions,
)
from app.services.competitor_profile_service import (
    get_competitor_profile,
)


class CompetitorArticleNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class ArticleCompetitorAnalysisResult:
    article_id: int
    company_id: int
    competitors: list[str]


async def analyze_article_competitors(
    db,
    *,
    article_id: int,
    company_id: int,
) -> ArticleCompetitorAnalysisResult:
    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        raise CompetitorArticleNotFoundError(
            f"Article {article_id} not found."
        )

    profile = await get_competitor_profile(
        db,
        company_id=company_id,
    )

    mentions: CompetitorMentionResult = (
        detect_competitor_mentions(
            article=article,
            profile=profile,
        )
    )

    await upsert_article_competitor_mentions(
        db,
        article_id=article.id,
        company_id=company_id,
        competitors=mentions.competitors,
    )

    return ArticleCompetitorAnalysisResult(
        article_id=article.id,
        company_id=company_id,
        competitors=mentions.competitors,
    )
