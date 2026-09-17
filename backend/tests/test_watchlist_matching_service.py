from types import SimpleNamespace

from app.services.watchlist_matching_service import (
    _matches,
)


def make_item(
    item_type: str,
    value: str,
):
    return SimpleNamespace(
        item_type=item_type,
        value=value,
    )


def make_row(**overrides):
    values = {
        "title": "RBI reviews digital payments company",
        "description": "Regulatory scrutiny continues.",
        "cleaned_content": "The Reserve Bank of India issued guidance.",
        "source_name": "Reuters",
        "event_type": "regulatory_action",
        "monitoring_topic": "payments regulation",
        "risk_level": "high",
        "business_impact": "regulatory",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_keyword_matches_article_text():
    assert _matches(
        make_item("keyword", "Reserve Bank"),
        make_row(),
    )


def test_regulator_uses_backward_compatible_text_match():
    assert _matches(
        make_item("regulator", "Reserve Bank of India"),
        make_row(),
    )


def test_source_matches_exactly_case_insensitive():
    assert _matches(
        make_item("source", "reuters"),
        make_row(),
    )


def test_source_does_not_use_partial_match():
    assert not _matches(
        make_item("source", "reut"),
        make_row(),
    )


def test_topic_matches_monitoring_topic():
    assert _matches(
        make_item("topic", "payments regulation"),
        make_row(),
    )


def test_topic_matches_event_type():
    assert _matches(
        make_item("topic", "regulatory_action"),
        make_row(),
    )


def test_risk_category_matches_stored_risk_level():
    assert _matches(
        make_item("risk_category", "HIGH"),
        make_row(),
    )


def test_impact_category_matches_primary_category():
    assert _matches(
        make_item("impact_category", "Regulatory"),
        make_row(),
    )


def test_unknown_item_type_does_not_invent_match():
    assert not _matches(
        make_item("something_custom", "RBI"),
        make_row(),
    )


def test_blank_value_does_not_match():
    assert not _matches(
        make_item("keyword", "   "),
        make_row(),
    )

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.services.watchlist_matching_service import (
    match_watchlist_items,
)


@pytest.mark.asyncio
async def test_match_watchlist_items_returns_company_scoped_matches():
    watchlist_item = SimpleNamespace(
        id=4,
        company_id=2,
        item_type="risk_category",
        item_name="High Risk",
        value="high",
        is_active=True,
    )

    article_row = SimpleNamespace(
        article_id=20,
        title="Payments company faces regulatory scrutiny",
        source_name="Reuters",
        url="https://example.com/20",
        published_at=datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
        description="Regulatory review underway.",
        cleaned_content="The company faces additional scrutiny.",
        event_type="regulatory_action",
        monitoring_topic="payments regulation",
        risk_level="high",
        risk_score=87.5,
        business_impact="regulatory",
    )

    watchlist_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [watchlist_item],
        ),
    )

    article_result = SimpleNamespace(
        all=lambda: [article_row],
    )

    db = AsyncMock()
    db.execute.side_effect = [
        watchlist_result,
        article_result,
    ]

    matches = await match_watchlist_items(
        db,
        company_id=2,
    )

    assert len(matches) == 1

    match = matches[0]

    assert match.watchlist_item_id == 4
    assert match.item_type == "risk_category"
    assert match.item_name == "High Risk"
    assert match.value == "high"
    assert match.article_id == 20
    assert match.title == (
        "Payments company faces regulatory scrutiny"
    )
    assert match.source_name == "Reuters"
    assert match.event_type == "regulatory_action"
    assert match.monitoring_topic == "payments regulation"
    assert match.risk_level == "high"
    assert match.risk_score == 87.5
    assert match.business_impact == "regulatory"

    assert db.execute.await_count == 2

    watchlist_sql = str(
        db.execute.await_args_list[0].args[0]
    )

    article_sql = str(
        db.execute.await_args_list[1].args[0]
    )

    assert "watchlist_items.company_id" in watchlist_sql
    assert "watchlist_items.is_active" in watchlist_sql

    assert "article_triages.company_id" in article_sql
    assert "risk_assessments.company_id" in article_sql
    assert "article_business_impacts.company_id" in article_sql


@pytest.mark.asyncio
async def test_match_watchlist_items_empty_watchlist_skips_article_query():
    watchlist_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [],
        ),
    )

    db = AsyncMock()
    db.execute.return_value = watchlist_result

    matches = await match_watchlist_items(
        db,
        company_id=2,
    )

    assert matches == []
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_match_watchlist_items_applies_publication_window():
    watchlist_item = SimpleNamespace(
        id=5,
        company_id=2,
        item_type="keyword",
        item_name="RBI",
        value="RBI",
        is_active=True,
    )

    watchlist_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: [watchlist_item],
        ),
    )

    article_result = SimpleNamespace(
        all=lambda: [],
    )

    db = AsyncMock()
    db.execute.side_effect = [
        watchlist_result,
        article_result,
    ]

    start = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )
    end = datetime(
        2026,
        9,
        17,
        tzinfo=timezone.utc,
    )

    matches = await match_watchlist_items(
        db,
        company_id=2,
        start=start,
        end=end,
    )

    assert matches == []

    article_statement = (
        db.execute.await_args_list[1].args[0]
    )
    article_sql = str(article_statement)

    assert "articles.published_at >=" in article_sql
    assert "articles.published_at <" in article_sql


@pytest.mark.asyncio
async def test_match_watchlist_items_honors_match_limit():
    watchlist_items = [
        SimpleNamespace(
            id=1,
            company_id=2,
            item_type="keyword",
            item_name="RBI",
            value="RBI",
            is_active=True,
        ),
        SimpleNamespace(
            id=2,
            company_id=2,
            item_type="risk_category",
            item_name="High",
            value="high",
            is_active=True,
        ),
    ]

    article_row = SimpleNamespace(
        article_id=30,
        title="RBI review",
        source_name="Reuters",
        url="https://example.com/30",
        published_at=None,
        description=None,
        cleaned_content="RBI announced a review.",
        event_type="regulatory_action",
        monitoring_topic=None,
        risk_level="high",
        risk_score=80.0,
        business_impact="regulatory",
    )

    db = AsyncMock()

    db.execute.side_effect = [
        SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: watchlist_items,
            ),
        ),
        SimpleNamespace(
            all=lambda: [article_row],
        ),
    ]

    matches = await match_watchlist_items(
        db,
        company_id=2,
        limit=1,
    )

    assert len(matches) == 1
    assert matches[0].watchlist_item_id == 1


@pytest.mark.asyncio
async def test_match_watchlist_items_rejects_invalid_company_id():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="company_id must be at least 1",
    ):
        await match_watchlist_items(
            db,
            company_id=0,
        )

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_match_watchlist_items_rejects_invalid_limit():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="limit must be at least 1",
    ):
        await match_watchlist_items(
            db,
            company_id=2,
            limit=0,
        )

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_match_watchlist_items_rejects_invalid_time_window():
    db = AsyncMock()

    start = datetime(
        2026,
        9,
        17,
        tzinfo=timezone.utc,
    )
    end = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="start must be earlier than end",
    ):
        await match_watchlist_items(
            db,
            company_id=2,
            start=start,
            end=end,
        )

    db.execute.assert_not_awaited()
