#!/usr/bin/env python3
"""Crawls the live BOAS catalogue and writes site/data.json + site/changelog.json.

Unlike scripts/bootstrap_fixtures.py (offline, fixture-based), this hits the
real site — see pipeline/fetch.py for the crawl. Still runs the bootstrap
path (previous_data=[]): real diffing against a prior data.json is issue
#4's scope.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.core import run_pipeline, write_output  # noqa: E402
from pipeline.fetch import crawl_catalogue  # noqa: E402

DOMAIN = "https://www.health-data-hub.fr"


def main() -> None:
    html_pages = crawl_catalogue(DOMAIN)

    result = run_pipeline(html_pages, previous_data=[])

    data_path = REPO_ROOT / "site" / "data.json"
    changelog_path = REPO_ROOT / "site" / "changelog.json"
    write_output(result, data_path, changelog_path)

    print(f"Wrote {len(result.new_data)} records to {data_path}")
    print(f"Wrote 1 changelog entry to {changelog_path}")


if __name__ == "__main__":
    main()
