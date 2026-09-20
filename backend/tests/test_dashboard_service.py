from unittest.mock import AsyncMock

import pytest

from app.services.dashboard_service import (
    get_dashboard_overview,
)


@pytest.mark.asyncio
async def test_dashboard_overview_separates_total_and_processed_articles():
    db = AsyncMock()

    db.scalar.side_effect = [
        46,  # total articles
        3,   # processed intelligence
        1,   # active companies
        1,   # high risk
        0,   # critical risk
        1,   # active alerts
        1,   # overdue alerts
    ]

    result = await get_dashboard_overview(db)

    assert result.total_articles == 46
    assert result.processed_articles == 3

    assert db.scalar.await_count == 7

    scalar_calls = db.scalar.await_args_list

    total_articles_sql = " ".join(
        str(scalar_calls[0].args[0]).lower().split()
    )

    processed_articles_sql = " ".join(
        str(scalar_calls[1].args[0]).lower().split()
    )

    assert "count(articles.id)" in total_articles_sql
    assert "from articles" in total_articles_sql
    assert "article_triages" not in total_articles_sql
    assert "articles.source_name in" not in total_articles_sql

    assert (
        "count(distinct(article_triages.article_id))"
        in processed_articles_sql
    )
    assert "from article_triages" in processed_articles_sql
    assert "join companies" in processed_articles_sql
    assert "companies.is_active" in processed_articles_sql

    assert total_articles_sql != processed_articles_sql
