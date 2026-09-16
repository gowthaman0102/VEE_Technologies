from app.models.article import Article
from app.services.competitor_mention_service import (
    detect_competitor_mentions,
)
from app.services.competitor_profile_service import (
    CompetitorProfile,
)


def make_article(
    *,
    title: str,
    content: str | None = None,
    description: str | None = None,
) -> Article:
    return Article(
        source_name="Test Source",
        source_type="manual",
        title=title,
        url="https://example.com/test",
        description=description,
        cleaned_content=content,
        extraction_status="success",
        embedding_status="pending",
    )


def test_detects_configured_competitors():
    article = make_article(
        title=(
            "Competitor One launches a new service"
        ),
        content=(
            "The market also includes Competitor Two."
        ),
    )

    profile = CompetitorProfile(
        company_id=2,
        competitors=[
            "Competitor One",
            "Competitor Two",
        ],
    )

    result = detect_competitor_mentions(
        article=article,
        profile=profile,
    )

    assert result.competitors == [
        "Competitor One",
        "Competitor Two",
    ]


def test_is_case_insensitive():
    article = make_article(
        title="competitor one expands",
    )

    profile = CompetitorProfile(
        company_id=2,
        competitors=[
            "Competitor One",
        ],
    )

    result = detect_competitor_mentions(
        article=article,
        profile=profile,
    )

    assert result.competitors == [
        "Competitor One",
    ]


def test_does_not_invent_unconfigured_competitors():
    article = make_article(
        title="Another Company announces expansion",
        content=(
            "Another Company entered the market."
        ),
    )

    profile = CompetitorProfile(
        company_id=2,
        competitors=[
            "Configured Competitor",
        ],
    )

    result = detect_competitor_mentions(
        article=article,
        profile=profile,
    )

    assert result.competitors == []


def test_empty_configuration_returns_empty():
    article = make_article(
        title="Any company name",
        content="Any content",
    )

    profile = CompetitorProfile(
        company_id=2,
        competitors=[],
    )

    result = detect_competitor_mentions(
        article=article,
        profile=profile,
    )

    assert result.competitors == []


def test_duplicate_mentions_return_once():
    article = make_article(
        title="Competitor One update",
        content=(
            "Competitor One was mentioned again. "
            "Competitor One continues expansion."
        ),
    )

    profile = CompetitorProfile(
        company_id=2,
        competitors=[
            "Competitor One",
        ],
    )

    result = detect_competitor_mentions(
        article=article,
        profile=profile,
    )

    assert result.competitors == [
        "Competitor One",
    ]
