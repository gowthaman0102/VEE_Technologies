from dataclasses import dataclass

from app.models.article import Article
from app.services.competitor_profile_service import (
    CompetitorProfile,
)


@dataclass(frozen=True)
class CompetitorMentionResult:
    competitors: list[str]


def detect_competitor_mentions(
    *,
    article: Article,
    profile: CompetitorProfile,
) -> CompetitorMentionResult:
    text = " ".join(
        part
        for part in [
            article.title,
            article.description,
            article.cleaned_content,
        ]
        if part
    ).casefold()

    mentioned = []

    for competitor in profile.competitors:
        normalized = competitor.strip()

        if not normalized:
            continue

        if normalized.casefold() in text:
            mentioned.append(normalized)

    return CompetitorMentionResult(
        competitors=mentioned,
    )
