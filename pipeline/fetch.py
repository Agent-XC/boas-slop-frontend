"""Live HTTP fetching: enumerates and retrieves the full catalogue from the
official site, for feeding into run_pipeline().

discover_detail_urls() is pure (no network) and unit tested against the
committed listing-page fixture. fetch_html() and crawl_catalogue() do real
network I/O and are deliberately not unit tested against the live site, per
the PRD's testing decision — verify these manually/live instead.
"""

import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "boas-slop-frontend/0.1 "
    "(+https://github.com/Agent-XC/boas-slop-frontend; "
    "unofficial BOAS catalogue mirror, weekly low-volume crawl)"
)

# Politeness delay between requests — this is a weekly, low-volume crawl
# (per DECISIONS.md's robots.txt check), not a bulk scrape.
REQUEST_DELAY_SECONDS = 0.5

CATALOGUE_PATH = "/bibliotheque-ouverte-algorithmes-sante"
_DETAIL_LINK_RE = re.compile(rf"^{re.escape(CATALOGUE_PATH)}/[^/?]+$")


def discover_detail_urls(listing_html: str, domain: str) -> list[str]:
    """Extracts detail-page URLs from one listing page's HTML.

    Matches only single-segment paths under the catalogue path (excludes
    the bare listing URL itself and pagination-only links like ?page=2),
    and de-duplicates while preserving order.
    """
    soup = BeautifulSoup(listing_html, "html.parser")
    seen: set[str] = set()
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if _DETAIL_LINK_RE.match(href) and href not in seen:
            seen.add(href)
            urls.append(urljoin(domain, href))
    return urls


def fetch_html(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.text


def crawl_catalogue(domain: str) -> dict[str, str]:
    """Fetches every current detail page from the live catalogue.

    Iterates listing pages (?page=0, 1, 2, ...) until a page yields no
    detail links, so new pages/projects are picked up automatically — no
    hardcoded page count or slug list. Requests are paced by
    REQUEST_DELAY_SECONDS to keep this a low-rate crawl.
    """
    catalogue_url = domain + CATALOGUE_PATH

    detail_urls: list[str] = []
    page = 0
    while True:
        listing_html = fetch_html(f"{catalogue_url}?page={page}")
        time.sleep(REQUEST_DELAY_SECONDS)
        page_urls = discover_detail_urls(listing_html, domain)
        if not page_urls:
            break
        detail_urls.extend(page_urls)
        page += 1

    html_pages = {}
    for url in detail_urls:
        html_pages[url] = fetch_html(url)
        time.sleep(REQUEST_DELAY_SECONDS)
    return html_pages
