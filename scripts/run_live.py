#!/usr/bin/env python3
"""Crawls the live BOAS catalogue and, on a real change, writes
site/data.json + site/changelog.json.

Unlike scripts/bootstrap_fixtures.py (offline, fixture-based, always
bootstrap), this hits the real site and diffs against whatever is already
committed in site/data.json — the first run (before that file exists) is
the bootstrap case; every run after that is a real diff.

Use --dry-run to see the decision (would it commit? what changed? why did
it abort?) without writing anything or touching the scraper-failure issue.
The write/no-write decision lives in pipeline.core.describe_and_maybe_write()
and the failure-issue decision in pipeline.failure_issue.handle_run_outcome();
this script is just the live-network wiring around both.
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.core import describe_and_maybe_write, run_pipeline  # noqa: E402
from pipeline.failure_issue import GitHubIssueClient  # noqa: E402
from pipeline.fetch import crawl_catalogue  # noqa: E402

DOMAIN = "https://www.health-data-hub.fr"
REPO = "Agent-XC/boas-slop-frontend"


def _load_previous_data(data_path: Path) -> list[dict]:
    if not data_path.exists():
        return []
    return json.loads(data_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Report the pipeline's decision without writing anything."
    )
    args = parser.parse_args()

    data_path = REPO_ROOT / "site" / "data.json"
    changelog_path = REPO_ROOT / "site" / "changelog.json"

    previous_data = _load_previous_data(data_path)
    html_pages = crawl_catalogue(DOMAIN)
    result = run_pipeline(html_pages, previous_data)

    outcome = describe_and_maybe_write(result, data_path, changelog_path, args.dry_run)
    print(outcome.message)

    if not args.dry_run:
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            print(GitHubIssueClient(REPO, token).handle_run_outcome(result.abort_reason))
        else:
            print("GITHUB_TOKEN not set — skipping scraper-failure issue handling.", file=sys.stderr)

    sys.exit(outcome.exit_code)


if __name__ == "__main__":
    main()
