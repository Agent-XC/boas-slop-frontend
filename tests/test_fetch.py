from conftest import load_fixture

from pipeline.fetch import discover_detail_urls

DOMAIN = "https://www.health-data-hub.fr"
CATALOGUE_URL = f"{DOMAIN}/bibliotheque-ouverte-algorithmes-sante"


def test_discover_detail_urls_finds_ten_links_excluding_base_and_pagination():
    html = load_fixture("listing_page_0.html")

    urls = discover_detail_urls(html, DOMAIN)

    assert len(urls) == 10
    assert f"{CATALOGUE_URL}/ehden-persephone" in urls
    assert CATALOGUE_URL not in urls  # the bare listing URL itself, not a detail page
    assert all("?" not in u for u in urls)  # pagination links (?page=N) are not detail pages


def test_discover_detail_urls_deduplicates():
    # The fixture's own markup already repeats every detail link twice
    # (mobile + desktop nav), so this exercises dedup without needing to
    # synthesize duplication.
    html = load_fixture("listing_page_0.html")
    urls = discover_detail_urls(html, DOMAIN)
    assert len(urls) == len(set(urls))
    assert len(urls) == 10
