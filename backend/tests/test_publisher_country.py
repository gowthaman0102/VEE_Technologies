from app.utils.publisher_country import resolve_publisher_country


def test_verified_domain_precedes_generic_tld():
    result = resolve_publisher_country(
        "Unknown",
        "Example",
        "https://www.npr.org/2026/example",
    )

    assert result.country_code == "US"
    assert result.country_name == "United States"
    assert result.verified is True


def test_google_news_wrapper_uses_source_metadata():
    result = resolve_publisher_country(
        "Google News - OpenAI",
        "OpenAI update - TechRadar",
        "https://news.google.com/articles/example",
        "https://www.techradar.com/news/example",
    )

    assert result.country_code == "GB"
    assert result.country_name == "United Kingdom"


def test_safe_cctld_resolution():
    result = resolve_publisher_country(
        "Regional source",
        "Example",
        "https://publisher.co.uk/example",
    )

    assert result.country_code == "GB"
    assert result.country_name == "United Kingdom"


def test_generic_com_remains_unknown():
    result = resolve_publisher_country(
        "Unverified source",
        "Example",
        "https://unverified.example.com/article",
    )

    assert result.country_name == "Unknown"
    assert result.verified is False
