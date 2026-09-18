import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from xml.etree import ElementTree
from urllib.parse import urljoin

import httpx

from app.ingestion.collectors.base import BaseCollector
from app.ingestion.types import CollectedArticle


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        attr_map = dict(attrs)
        href = (attr_map.get("href") or "").strip()
        self._current = {"href": href, "text": ""}

    def handle_data(self, data):
        if self._current is not None:
            self._current["text"] += data

    def handle_endtag(self, tag):
        if tag.lower() != "a" or self._current is None:
            return

        href = self._current.get("href", "").strip()
        text = " ".join(self._current.get("text", "").split())
        self.links.append({"href": href, "text": text})
        self._current = None


class HTMLListingCollector(BaseCollector):
    def __init__(
        self,
        listing_url: str,
        source_name: str,
        language: str | None = None,
        timeout: float = 20.0,
        base_url: str | None = None,
    ) -> None:
        if not listing_url.strip():
            raise ValueError("HTML listing URL is required")

        if not source_name.strip():
            raise ValueError("HTML listing source name is required")

        if timeout <= 0:
            raise ValueError("HTML listing timeout must be greater than zero")

        self.listing_url = listing_url
        self.source_name = source_name
        self.language = language
        self.timeout = timeout
        self.base_url = (base_url or listing_url).rstrip("/")

    async def collect(self) -> list[CollectedArticle]:
        if self.listing_url.lower().endswith(".xml") or "sitemap" in self.listing_url.lower():
            return await self._collect_from_sitemap()

        return await self._collect_from_html_listing()

    async def _collect_from_sitemap(self) -> list[CollectedArticle]:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            response = await client.get(self.listing_url)
            response.raise_for_status()
            xml = response.text

        root = ElementTree.fromstring(xml)
        items: list[CollectedArticle] = []
        seen: set[str] = set()

        for url_element in root.iter():
            if url_element.tag.rsplit("}", 1)[-1] != "url":
                continue

            loc = url_element.findtext("{*}loc")
            if loc is None:
                loc = url_element.findtext("loc")
            if not loc:
                continue

            url = urljoin(self.listing_url, loc.strip())
            if not self._looks_like_press_release(url):
                continue

            if url in seen:
                continue
            seen.add(url)

            published_at = None
            lastmod = url_element.findtext("{*}lastmod")
            if lastmod is None:
                lastmod = url_element.findtext("lastmod")
            if lastmod:
                try:
                    published_at = datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
                except ValueError:
                    published_at = None

            items.append(
                CollectedArticle(
                    source_name=self.source_name,
                    source_type="html_listing",
                    external_id=url,
                    title=self._slug_to_title(url),
                    url=url,
                    author=None,
                    description=self._slug_to_title(url),
                    raw_content=None,
                    language=self.language,
                    published_at=published_at,
                )
            )

        return items

    async def _collect_from_html_listing(self) -> list[CollectedArticle]:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            response = await client.get(self.listing_url)
            response.raise_for_status()
            html = response.text

        parser = _AnchorParser()
        parser.feed(html)
        articles: list[CollectedArticle] = []
        seen: set[str] = set()

        for link in parser.links:
            href = link.get("href", "").strip()
            if not href:
                continue

            normalized = href.split("#", 1)[0]
            if not normalized:
                continue

            href_abs = urljoin(self.listing_url, normalized)
            if not self._looks_like_press_release(href_abs):
                continue

            title = link.get("text", "").strip()
            if not title:
                continue

            key = href_abs.lower()
            if key in seen:
                continue
            seen.add(key)

            published_at = self._extract_date_from_url_or_text(href_abs)

            articles.append(
                CollectedArticle(
                    source_name=self.source_name,
                    source_type="html_listing",
                    external_id=href_abs,
                    title=title,
                    url=href_abs,
                    author=None,
                    description=title,
                    raw_content=None,
                    language=self.language,
                    published_at=published_at,
                )
            )

        return articles

    @staticmethod
    def _slug_to_title(url: str) -> str:
        path = url.split("?", 1)[0].split("#", 1)[0].rsplit("/", 1)[-1]
        name = path.rsplit(".", 1)[0]
        if not name:
            return "Official article"

        title = name.replace("-", " ")
        title = re.sub(r"\s+", " ", title).strip()
        return title.title()

    @staticmethod
    def _looks_like_press_release(url: str) -> bool:
        lowered = url.lower()
        if not (
            "/newsroom/press-releases/" in lowered
            or "/newsroom/vee-technologies-in-the-news/" in lowered
            or "/newsroom/" in lowered
            or "/blog/" in lowered
        ):
            return False

        return "veetechnologies.com" in lowered and not lowered.endswith(".pdf")

    @staticmethod
    def _extract_date_from_url_or_text(url: str) -> datetime | None:
        match = re.search(r"(\d{4})/(\d{2})/(\d{2})", url)
        if match:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
        return None
