import pytest

from app.ingestion.multi_runner import run_sources
from app.ingestion.runner import IngestionResult
from app.ingestion.sources import NewsSource


@pytest.mark.asyncio
async def test_run_sources_collects_results(monkeypatch):
    sources = [
        NewsSource(
            key="rss_one",
            name="RSS One",
            source_type="rss",
            url="https://example.com/rss",
        ),
        NewsSource(
            key="rss_two",
            name="RSS Two",
            source_type="rss",
            url="https://example.com/rss2",
        ),
    ]

    class FakeCollector:
        pass

    def fake_build_collector(*args, **kwargs):
        return FakeCollector()

    async def fake_run_collector(
        db,
        collector,
        limit=None,
    ):
        return IngestionResult(
            collected=5,
            inserted=3,
            skipped=2,
            inserted_article_ids=[
                301,
                302,
                303,
            ],
        )

    monkeypatch.setattr(
        "app.ingestion.multi_runner.build_collector",
        fake_build_collector,
    )

    monkeypatch.setattr(
        "app.ingestion.multi_runner.run_collector",
        fake_run_collector,
    )

    results = await run_sources(
        db=None,
        sources=sources,
        per_source_limit=10,
    )

    assert len(results) == 2

    assert results[0].source_key == "rss_one"
    assert results[0].collected == 5
    assert results[0].inserted == 3
    assert results[0].skipped == 2
    assert results[0].inserted_article_ids == [
        301,
        302,
        303,
    ]
    assert results[0].error is None


@pytest.mark.asyncio
async def test_run_sources_continues_after_failure(monkeypatch):
    sources = [
        NewsSource(
            key="bad_source",
            name="Bad Source",
            source_type="rss",
            url="https://example.com/bad",
        ),
        NewsSource(
            key="good_source",
            name="Good Source",
            source_type="rss",
            url="https://example.com/good",
        ),
    ]

    def fake_build_collector(source, **kwargs):
        if source.key == "bad_source":
            raise RuntimeError("Source failed")

        return object()

    async def fake_run_collector(
        db,
        collector,
        limit=None,
    ):
        return IngestionResult(
            collected=2,
            inserted=2,
            skipped=0,
            inserted_article_ids=[
                401,
                402,
            ],
        )

    monkeypatch.setattr(
        "app.ingestion.multi_runner.build_collector",
        fake_build_collector,
    )

    monkeypatch.setattr(
        "app.ingestion.multi_runner.run_collector",
        fake_run_collector,
    )

    results = await run_sources(
        db=None,
        sources=sources,
    )

    assert len(results) == 2

    assert results[0].source_key == "bad_source"
    assert results[0].error == "Source failed"

    assert results[1].source_key == "good_source"
    assert results[1].inserted == 2
    assert results[1].inserted_article_ids == [
        401,
        402,
    ]
    assert results[1].error is None
