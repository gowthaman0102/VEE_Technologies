import re
from dataclasses import dataclass
from typing import Optional

from app.utils.publisher_country_registry import (
    PUBLISHER_COUNTRY_BY_DOMAIN,
    PUBLISHER_COUNTRY_BY_NAME,
)

@dataclass
class PublisherCountryResult:
    country_code: Optional[str]
    country_name: Optional[str]
    method: str

from urllib.parse import urlsplit

def resolve_publisher_country(
    publisher_name: Optional[str],
    publisher_domain: Optional[str],
    source_metadata: Optional[dict] = None,
    canonical_url: Optional[str] = None
) -> PublisherCountryResult:
    
    # 1. Manual override / Source metadata
    if source_metadata and "country_code" in source_metadata:
        return PublisherCountryResult(
            country_code=source_metadata["country_code"],
            country_name=source_metadata.get("country_name", "Unknown"),
            method="source_metadata"
        )
        
    # Ignore aggregator domains
    ignored_domains = {"news.google.com", "news.yahoo.com", "msn.com"}
    
    domain = None
    if publisher_domain:
        d = publisher_domain.lower().replace("www.", "")
        if d not in ignored_domains:
            domain = d
            
    if not domain and canonical_url:
        try:
            d = urlsplit(canonical_url).hostname
            if d:
                d = d.lower().replace("www.", "")
                if d not in ignored_domains:
                    domain = d
        except ValueError:
            pass

    # 2. Domain registry
    if domain:
        if domain in PUBLISHER_COUNTRY_BY_DOMAIN:
            reg = PUBLISHER_COUNTRY_BY_DOMAIN[domain]
            return PublisherCountryResult(
                country_code=reg["country_code"],
                country_name=reg["country_name"],
                method="domain_registry"
            )
            
    # 3. Name mapping fallback
    if publisher_name:
        name_lower = publisher_name.lower().strip()
        if name_lower in PUBLISHER_COUNTRY_BY_NAME:
            reg = PUBLISHER_COUNTRY_BY_NAME[name_lower]
            return PublisherCountryResult(
                country_code=reg["country_code"],
                country_name=reg["country_name"],
                method="manual_registry"
            )

    # 4. ccTLD Fallback
    if domain:
        if domain.endswith(".in") or domain.endswith(".co.in"):
            return PublisherCountryResult("IN", "India", "cctld")
        elif domain.endswith(".uk") or domain.endswith(".co.uk"):
            return PublisherCountryResult("GB", "United Kingdom", "cctld")
        elif domain.endswith(".au") or domain.endswith(".com.au"):
            return PublisherCountryResult("AU", "Australia", "cctld")
        elif domain.endswith(".ca") or domain.endswith(".com.ca"):
            return PublisherCountryResult("CA", "Canada", "cctld")
        elif domain.endswith(".de"):
            return PublisherCountryResult("DE", "Germany", "cctld")
        elif domain.endswith(".fr"):
            return PublisherCountryResult("FR", "France", "cctld")
        elif domain.endswith(".jp") or domain.endswith(".co.jp"):
            return PublisherCountryResult("JP", "Japan", "cctld")
        elif domain.endswith(".sg") or domain.endswith(".com.sg"):
            return PublisherCountryResult("SG", "Singapore", "cctld")
        elif domain.endswith(".ie") or domain.endswith(".co.ie"):
            return PublisherCountryResult("IE", "Ireland", "cctld")
        elif domain.endswith(".nz") or domain.endswith(".co.nz"):
            return PublisherCountryResult("NZ", "New Zealand", "cctld")

    # 5. Unknown
    return PublisherCountryResult(None, "Unknown", "unknown")

