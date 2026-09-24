from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from app.utils.article_metadata import publisher_name


@dataclass(frozen=True)
class PublisherCountryResult:
    country_code: str | None
    country_name: str
    resolution_method: str
    verified: bool


_VERIFIED_PUBLISHERS: dict[str, tuple[str, str]] = {
    "bbc": ("GB", "United Kingdom"),
    "bbc news": ("GB", "United Kingdom"),
    "the guardian": ("GB", "United Kingdom"),
    "the times of india": ("IN", "India"),
    "times of india": ("IN", "India"),
    "indian express": ("IN", "India"),
    "business standard": ("IN", "India"),
    "businessline": ("IN", "India"),
    "the hindu": ("IN", "India"),
    "reuters": ("GB", "United Kingdom"),
    "cbc": ("CA", "Canada"),
    "cbc news": ("CA", "Canada"),
    "cnbc": ("US", "United States"),
    "cnn": ("US", "United States"),
    "npr": ("US", "United States"),
    "the new york times": ("US", "United States"),
    "new york times": ("US", "United States"),
    "the washington post": ("US", "United States"),
    "washingtonpost.com": ("US", "United States"),
    "bloomberg": ("US", "United States"),
    "forbes": ("US", "United States"),
    "techcrunch": ("US", "United States"),
    "wired": ("US", "United States"),
    "abc news": ("US", "United States"),
    "ap news": ("US", "United States"),
    "associated press": ("US", "United States"),
    "axios": ("US", "United States"),
    "business insider": ("US", "United States"),
    "cbs news": ("US", "United States"),
    "fox news": ("US", "United States"),
    "los angeles times": ("US", "United States"),
    "new york post": ("US", "United States"),
    "nbc news": ("US", "United States"),
    "politico": ("US", "United States"),
    "usa today": ("US", "United States"),
    "wall street journal": ("US", "United States"),
    "wsj": ("US", "United States"),
    "washington examiner": ("US", "United States"),
    "financial times": ("GB", "United Kingdom"),
    "the independent": ("GB", "United Kingdom"),
    "the irish times": ("IE", "Ireland"),
    "rte": ("IE", "Ireland"),
    "dw": ("DE", "Germany"),
    "dw (english)": ("DE", "Germany"),
    "cna": ("SG", "Singapore"),
    "scmp": ("HK", "Hong Kong"),
    "south china morning post": ("HK", "Hong Kong"),
    "arab news": ("SA", "Saudi Arabia"),
    "al jazeera": ("QA", "Qatar"),
    "al jazeera english": ("QA", "Qatar"),
    "haaretz": ("IL", "Israel"),
    "new zealand herald": ("NZ", "New Zealand"),
    "the punch": ("NG", "Nigeria"),
    "the times": ("GB", "United Kingdom"),
    "the verge": ("US", "United States"),
    "abcnews": ("US", "United States"),
    "apnews": ("US", "United States"),
    "appleinsider": ("US", "United States"),
    "arstechnica": ("US", "United States"),
    "cnet": ("US", "United States"),
    "engadget": ("US", "United States"),
    "fortune": ("US", "United States"),
    "gizmodo": ("US", "United States"),
    "hackaday": ("US", "United States"),
    "mashable": ("US", "United States"),
    "marketwatch": ("US", "United States"),
    "pcmag": ("US", "United States"),
    "prnewswire": ("US", "United States"),
    "pbs": ("US", "United States"),
    "qz": ("US", "United States"),
    "scientific american": ("US", "United States"),
    "seeking alpha": ("US", "United States"),
    "siliconangle": ("US", "United States"),
    "techrepublic": ("US", "United States"),
    "techspot": ("US", "United States"),
    "the atlantic": ("US", "United States"),
    "the information": ("US", "United States"),
    "the new yorker": ("US", "United States"),
    "the next web": ("NL", "Netherlands"),
    "venturebeat": ("US", "United States"),
    "vox": ("US", "United States"),
    "yahoo": ("US", "United States"),
    "yahoo finance": ("US", "United States"),
    "yahoo tech": ("US", "United States"),
    "wired": ("US", "United States"),
    "z t net": ("US", "United States"),
    "the decoder": ("DE", "Germany"),
    "the journal ie": ("IE", "Ireland"),
    "thejournal ie": ("IE", "Ireland"),
    "the independent": ("GB", "United Kingdom"),
    "the hill": ("US", "United States"),
    "the register": ("GB", "United Kingdom"),
    "tom s hardware": ("US", "United States"),
    "tomshardware": ("US", "United States"),
    "theregister": ("GB", "United Kingdom"),
    "the hacker news": ("US", "United States"),
    "thehackernews": ("US", "United States"),
    "thehealthcaretechnologyreport": ("US", "United States"),
    "washington examiner": ("US", "United States"),
    "washingtonpost": ("US", "United States"),
    "nypost": ("US", "United States"),
    "openai": ("US", "United States"),
    "microsoft": ("US", "United States"),
    "mit technology review": ("US", "United States"),
    "harvard school of engineering and applied sciences": ("US", "United States"),
}

_TLD_COUNTRIES: dict[str, tuple[str, str]] = {
    "in": ("IN", "India"),
    "co.in": ("IN", "India"),
    "uk": ("GB", "United Kingdom"),
    "co.uk": ("GB", "United Kingdom"),
    "ca": ("CA", "Canada"),
    "de": ("DE", "Germany"),
    "fr": ("FR", "France"),
    "jp": ("JP", "Japan"),
    "sg": ("SG", "Singapore"),
    "au": ("AU", "Australia"),
    "com.au": ("AU", "Australia"),
}

_VERIFIED_DOMAINS: dict[str, tuple[str, str]] = {
    "pypi.org": ("US", "United States"),
    "biztoc.com": ("US", "United States"),
    "cryptobriefing.com": ("US", "United States"),
    "slashdot.org": ("US", "United States"),
    "247wallst.com": ("US", "United States"),
    "techradar.com": ("GB", "United Kingdom"),
    "forkast.news": ("HK", "Hong Kong"),
    "finance.yahoo.com": ("US", "United States"),
    "tech.yahoo.com": ("US", "United States"),
    "businessinsider.com": ("US", "United States"),
    "africa.businessinsider.com": ("US", "United States"),
    "breitbart.com": ("US", "United States"),
    "digitaljournal.com": ("CA", "Canada"),
    "pymnts.com": ("US", "United States"),
    "americanthinker.com": ("US", "United States"),
    "aws.amazon.com": ("US", "United States"),
    "futurism.com": ("US", "United States"),
    "news.bloomberglaw.com": ("US", "United States"),
    "thurrott.com": ("US", "United States"),
    "github.com": ("US", "United States"),
    "naturalnews.com": ("US", "United States"),
    "freerepublic.com": ("US", "United States"),
    "deadline.com": ("US", "United States"),
    "techxplore.com": ("US", "United States"),
    "psychologytoday.com": ("US", "United States"),
    "decrypt.co": ("US", "United States"),
    "financialpost.com": ("CA", "Canada"),
    "insurancejournal.com": ("US", "United States"),
    "helpnetsecurity.com": ("US", "United States"),
    "calcalistech.com": ("IL", "Israel"),
    "kpbs.org": ("US", "United States"),
    "stratechery.com": ("US", "United States"),
    "truthout.org": ("US", "United States"),
    "seattletimes.com": ("US", "United States"),
    "9to5mac.com": ("US", "United States"),
    "turnpanel.com": ("US", "United States"),
    "africasacountry.com": ("US", "United States"),
    "wkbn.com": ("US", "United States"),
    "tbray.org": ("US", "United States"),
    "hothardware.com": ("US", "United States"),
    "wccftech.com": ("US", "United States"),
    "commondreams.org": ("US", "United States"),
    "news.livedoor.com": ("JP", "Japan"),
    "cryptoslate.com": ("US", "United States"),
    "memphisflyer.com": ("US", "United States"),
    "artificiallawyer.com": ("GB", "United Kingdom"),
    "abajournal.com": ("US", "United States"),
    "securityweek.com": ("US", "United States"),
    "bizjournals.com": ("US", "United States"),
    "logisticsviewpoints.com": ("US", "United States"),
    "newsnationnow.com": ("US", "United States"),
    "infoq.com": ("US", "United States"),
    "crn.com": ("US", "United States"),
    "legaltechnology.com": ("US", "United States"),
    "constellationr.com": ("US", "United States"),
    "siouxlandnews.com": ("US", "United States"),
    "the-decoder.com": ("DE", "Germany"),
    "cybernews.com": ("US", "United States"),
    "theinformation.com": ("US", "United States"),
    "eciks.org": ("US", "United States"),
    "blockspace.media": ("US", "United States"),
    "livenowfox.com": ("US", "United States"),
    "aljazeera.com": ("QA", "Qatar"),
    "abcnews.com": ("US", "United States"),
    "apnews.com": ("US", "United States"),
    "axios.com": ("US", "United States"),
    "businessinsider.com": ("US", "United States"),
    "cbsnews.com": ("US", "United States"),
    "cnn.com": ("US", "United States"),
    "foxnews.com": ("US", "United States"),
    "latimes.com": ("US", "United States"),
    "nbcnews.com": ("US", "United States"),
    "npr.org": ("US", "United States"),
    "nytimes.com": ("US", "United States"),
    "nypost.com": ("US", "United States"),
    "politico.com": ("US", "United States"),
    "usatoday.com": ("US", "United States"),
    "wsj.com": ("US", "United States"),
    "washingtonexaminer.com": ("US", "United States"),
    "washingtonpost.com": ("US", "United States"),
    "bbc.com": ("GB", "United Kingdom"),
    "bbc.co.uk": ("GB", "United Kingdom"),
    "ft.com": ("GB", "United Kingdom"),
    "theguardian.com": ("GB", "United Kingdom"),
    "independent.co.uk": ("GB", "United Kingdom"),
    "reuters.com": ("GB", "United Kingdom"),
    "cbc.ca": ("CA", "Canada"),
    "business-standard.com": ("IN", "India"),
    "businessline.global": ("IN", "India"),
    "indianexpress.com": ("IN", "India"),
    "timesofindia.indiatimes.com": ("IN", "India"),
    "dw.com": ("DE", "Germany"),
    "aljazeera.com": ("QA", "Qatar"),
    "scmp.com": ("HK", "Hong Kong"),
    "haaretz.com": ("IL", "Israel"),
    "thehindu.com": ("IN", "India"),
}


def resolve_publisher_country(
    source_name: str,
    title: str,
    url: str | None,
    canonical_url: str | None = None,
) -> PublisherCountryResult:
    display_name = publisher_name(source_name, title, url or "", canonical_url)
    name = _normalize_publisher(display_name)
    verified = _VERIFIED_PUBLISHERS.get(name)
    if verified is None:
        verified = next(
            (
                country
                for publisher, country in _VERIFIED_PUBLISHERS.items()
                if _normalize_publisher(publisher) == name
            ),
            None,
        )
    if verified:
        return PublisherCountryResult(*verified, "verified_publisher_override", True)

    for candidate in (canonical_url, url):
        hostname = _hostname(candidate)
        if not hostname or hostname == "news.google.com":
            continue
        verified_domain = _VERIFIED_DOMAINS.get(hostname)
        if verified_domain:
            return PublisherCountryResult(
                *verified_domain,
                "verified_publisher_domain",
                True,
            )
        suffix = ".".join(hostname.split(".")[-2:])
        if suffix in _TLD_COUNTRIES:
            code, country = _TLD_COUNTRIES[suffix]
            return PublisherCountryResult(code, country, "verified_cctld", True)
        suffix = hostname.rsplit(".", 1)[-1]
        if suffix in _TLD_COUNTRIES:
            code, country = _TLD_COUNTRIES[suffix]
            return PublisherCountryResult(code, country, "verified_cctld", True)

    return PublisherCountryResult(None, "Unknown", "unresolved", False)


def _normalize_publisher(value: str) -> str:
    normalized = re.sub(r"\.(?:com|org|net|co|io|ai)$", "", value.lower().strip())
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def canonical_publisher_domain(
    url: str | None,
    canonical_url: str | None = None,
) -> str | None:
    for candidate in (canonical_url, url):
        hostname = _hostname(candidate)
        if hostname and hostname != "news.google.com":
            return hostname.removeprefix("www.")
    return None


def _hostname(url: str | None) -> str | None:
    try:
        return (
            (urlsplit(url or "").hostname or "")
            .lower()
            .removeprefix("www.")
            .rstrip(".")
        )
    except ValueError:
        return None
