#!/usr/bin/env python3
"""Generates site/data.json and site/changelog.json from the committed
detail-page fixtures in tests/fixtures/.

This is the tracer-bullet bootstrap: it reads fixtures, not the live site —
live fetching and full-catalogue discovery are issue #3's scope. Real
diffing against a prior data.json is issue #4's scope; this script always
runs the bootstrap path (previous_data=[]).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.core import run_pipeline, write_output  # noqa: E402

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
BASE_URL = "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/"

# Real, scraped fixtures only — the synthetic related_to test fixtures are
# excluded from the actual site dataset.
DETAIL_FIXTURES = {
    "ehden-persephone": "detail_ehden-persephone.html",
    "algorithme-pour-construire-le-top-diabete-de-la-cartographie": "detail_top-diabete.html",
    "cartographie-des-pathologies-et-des-depenses-version-g12": "detail_cartographie-g12.html",
    "eds-nlp-framework-de-nlp-modulaire-et-rapide-compatible-avec": "detail_eds-nlp.html",
}


def main() -> None:
    html_pages = {
        BASE_URL + slug: (FIXTURES_DIR / filename).read_text(encoding="utf-8")
        for slug, filename in DETAIL_FIXTURES.items()
    }

    result = run_pipeline(html_pages, previous_data=[])

    data_path = REPO_ROOT / "site" / "data.json"
    changelog_path = REPO_ROOT / "site" / "changelog.json"
    write_output(result, data_path, changelog_path)

    print(f"Wrote {len(result.new_data)} records to {data_path}")
    print(f"Wrote 1 changelog entry to {changelog_path}")


if __name__ == "__main__":
    main()
