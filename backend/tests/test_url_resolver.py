from app.processing import url_resolver


def test_is_google_news_url():
    assert url_resolver.is_google_news_url(
        "https://news.google.com/rss/articles/test"
    ) is True

    assert url_resolver.is_google_news_url(
        "https://example.com/article"
    ) is False


def test_resolve_non_google_url():
    url = "https://example.com/article"

    assert (
        url_resolver.resolve_article_url(url)
        == url
    )


def test_resolve_google_news_url(
    monkeypatch,
):
    google_url = (
        "https://news.google.com/"
        "rss/articles/test"
    )

    monkeypatch.setattr(
        url_resolver,
        "new_decoderv1",
        lambda url: {
            "status": True,
            "decoded_url": (
                "https://publisher.example.com/article"
            ),
        },
    )

    assert (
        url_resolver.resolve_article_url(
            google_url
        )
        == (
            "https://publisher.example.com/article"
        )
    )


def test_resolver_failure_falls_back(
    monkeypatch,
):
    google_url = (
        "https://news.google.com/"
        "rss/articles/test"
    )

    def fail(_):
        raise RuntimeError(
            "decoder unavailable"
        )

    monkeypatch.setattr(
        url_resolver,
        "new_decoderv1",
        fail,
    )

    assert (
        url_resolver.resolve_article_url(
            google_url
        )
        == google_url
    )
