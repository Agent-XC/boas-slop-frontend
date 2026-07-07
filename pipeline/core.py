"""The pipeline's single tested seam.

run_pipeline() takes raw detail-page HTML and the previously-committed
dataset, and returns everything needed to decide what to write: the new
dataset, a diff, a commit/abort decision, and a changelog entry. No
network, git, or GitHub-API calls happen inside it.

This slice only implements the bootstrap path (previous_data == []):
everything parsed is "added", related_to is computed fresh across the new
records, and should_commit is always True (there is nothing yet to compare
counts/field-completeness against). Real diffing against a non-empty
previous_data (added/removed/changed/renamed classification and the abort
thresholds) is out of scope here — see issue #4 ("Diff engine").
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pipeline.parse import parse_detail_page


@dataclass
class PipelineResult:
    new_data: list[dict]
    diff: dict
    should_commit: bool
    abort_reason: str | None
    changelog_entry: dict | None = field(default=None)


def write_output(result: PipelineResult, data_path: Path, changelog_path: Path) -> None:
    """Writes a PipelineResult's data.json + changelog.json to the given paths.

    Shared by the fixture-based and live-crawl entrypoints so the output
    format only needs to change in one place.
    """
    data_path.write_text(json.dumps(result.new_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changelog_path.write_text(
        json.dumps([result.changelog_entry], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _compute_related_to(records: list[dict]) -> None:
    """Sets related_to on each record: other slugs sharing the same repo URL."""
    by_repo: dict[str, list[str]] = {}
    for record in records:
        repo = record["code_disponible_sur"]
        if not repo:
            continue
        by_repo.setdefault(repo, []).append(record["slug"])

    for record in records:
        repo = record["code_disponible_sur"]
        siblings = by_repo.get(repo, [])
        record["related_to"] = [slug for slug in siblings if slug != record["slug"]]


def run_pipeline(html_pages: dict[str, str], previous_data: list[dict]) -> PipelineResult:
    if previous_data:
        raise NotImplementedError(
            "Diffing against a non-empty previous_data is issue #4's scope; "
            "this slice only supports the bootstrap case (previous_data=[])."
        )

    now = datetime.now(timezone.utc).isoformat()
    records = [parse_detail_page(html, url) for url, html in html_pages.items()]
    for record in records:
        record["last_checked"] = now
    _compute_related_to(records)

    added_slugs = [record["slug"] for record in records]

    return PipelineResult(
        new_data=records,
        diff={"added": added_slugs, "removed": [], "changed": [], "renamed": []},
        should_commit=True,
        abort_reason=None,
        changelog_entry={
            "date": now,
            "added": added_slugs,
            "removed": [],
            "changed": [],
            "renamed": [],
        },
    )
