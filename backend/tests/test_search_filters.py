from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.search_filters import SearchFilters


def test_search_filters_defaults_to_unfiltered():
    filters = SearchFilters()

    assert filters.start is None
    assert filters.end is None
    assert filters.source_name is None
    assert filters.sentiment is None
    assert filters.risk_level is None
    assert filters.business_impact is None
    assert filters.event_type is None
    assert filters.event_cluster_id is None


def test_search_filters_accepts_all_supported_filters():
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

    filters = SearchFilters(
        start=start,
        end=end,
        source_name="Reuters",
        sentiment="negative",
        risk_level="high",
        business_impact="regulatory",
        event_type="regulatory",
        event_cluster_id=7,
    )

    assert filters.start == start
    assert filters.end == end
    assert filters.source_name == "Reuters"
    assert filters.sentiment == "negative"
    assert filters.risk_level == "high"
    assert filters.business_impact == "regulatory"
    assert filters.event_type == "regulatory"
    assert filters.event_cluster_id == 7


def test_search_filters_strips_optional_text():
    filters = SearchFilters(
        source_name="  Reuters  ",
        sentiment="  negative ",
        risk_level=" high ",
        business_impact=" regulatory ",
        event_type=" enforcement ",
    )

    assert filters.source_name == "Reuters"
    assert filters.sentiment == "negative"
    assert filters.risk_level == "high"
    assert filters.business_impact == "regulatory"
    assert filters.event_type == "enforcement"


def test_search_filters_converts_blank_text_to_none():
    filters = SearchFilters(
        source_name="   ",
        sentiment="",
        risk_level=" ",
        business_impact="  ",
        event_type="   ",
    )

    assert filters.source_name is None
    assert filters.sentiment is None
    assert filters.risk_level is None
    assert filters.business_impact is None
    assert filters.event_type is None


def test_search_filters_rejects_invalid_time_window():
    timestamp = datetime(
        2026,
        9,
        17,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValidationError,
        match="start must be earlier than end",
    ):
        SearchFilters(
            start=timestamp,
            end=timestamp,
        )


def test_search_filters_rejects_invalid_cluster_id():
    with pytest.raises(ValidationError):
        SearchFilters(
            event_cluster_id=0,
        )
