from dataclasses import dataclass

import httpx
import trafilatura

from app.processing.normalization import clean_text


@dataclass
class ExtractionResult:
    success: bool
    content: str | None
    error: str | None
    final_url: str | None = None


class ArticleExtractor:
    def __init__(
        self,
        timeout: float = 15.0,
        user_agent: str = (
            "Mozilla/5.0 "
            "(compatible; AI-Media-Intelligence/0.1)"
        ),
    ) -> None:
        if timeout <= 0:
            raise ValueError(
                "Extraction timeout must be greater than zero"
            )

        self.timeout = timeout
        self.user_agent = user_agent

    async def extract_from_url(
        self,
        url: str,
    ) -> ExtractionResult:
        if not url.strip():
            return ExtractionResult(
                success=False,
                content=None,
                error="Article URL is required",
            )

        try:
            html, final_url = await self._fetch(
                url
            )
        except httpx.TimeoutException:
            return ExtractionResult(
                success=False,
                content=None,
                error="Article fetch timed out",
            )
        except httpx.HTTPStatusError as exc:
            return ExtractionResult(
                success=False,
                content=None,
                error=(
                    "Article fetch failed with "
                    f"HTTP {exc.response.status_code}"
                ),
                final_url=str(
                    exc.response.url
                ),
            )
        except httpx.RequestError as exc:
            return ExtractionResult(
                success=False,
                content=None,
                error=(
                    "Article fetch failed: "
                    f"{type(exc).__name__}"
                ),
            )

        content = self.extract_from_html(
            html
        )

        if not content:
            return ExtractionResult(
                success=False,
                content=None,
                error="No article content extracted",
                final_url=final_url,
            )

        return ExtractionResult(
            success=True,
            content=content,
            error=None,
            final_url=final_url,
        )

    async def _fetch(
        self,
        url: str,
    ) -> tuple[str, str]:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": self.user_agent,
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml"
                ),
            },
        ) as client:
            response = await client.get(
                url
            )

            response.raise_for_status()

            return (
                response.text,
                str(response.url),
            )

    @staticmethod
    def extract_from_html(
        html: str,
    ) -> str:
        if not html.strip():
            return ""

        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )

        return clean_text(
            extracted
        )
