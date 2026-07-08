"""The pipeline's single tested seam.

run_pipeline() takes raw detail-page HTML and the previously-committed
dataset, and returns everything needed to decide what to write: the new
dataset, a diff, a commit/abort decision, and a changelog entry. No
network, git, or GitHub-API calls happen inside it.

When previous_data is empty, everything is classified as "added" (the
bootstrap case). Otherwise a real diff is computed against previous_data:
added / removed / changed (per field, excluding last_checked which always
differs) / renamed (a disappeared slug and an appeared slug sharing the
same code_disponible_sur, only when that pairing is unambiguous — see
_compute_diff). related_to is recomputed fresh every run regardless of what
previous_data says. The run aborts (should_commit=False, abort_reason set,
no changelog entry) if the project count drops at all, or if a required
field (titre, slug, code_disponible_sur) is missing on more than 10% of
rows. A run with zero real differences also doesn't commit, but with
abort_reason=None — distinct from an actual threshold failure (issue #5's
failure-issue reuse needs to tell these apart).
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pipeline.parse import parse_detail_page

# Compared field-by-field between an existing record and its new version to
# detect "changed". Excludes slug (identity, handled via rename detection)
# and last_checked (updates every run regardless of real content changes).
_COMPARABLE_FIELDS = (
    "titre",
    "type_auteur",
    "objectif",
    "domaine_medical",
    "langage",
    "donnees_application",
    "validation",
    "maintenance",
    "code_disponible_sur",
    "url_fiche_boas_source",
    "related_to",
)

_REQUIRED_FIELDS = ("titre", "slug", "code_disponible_sur")
_MISSING_FIELD_ABORT_RATIO = 0.10

# Friendlier French (singular, plural) labels for the changelog summary;
# fields not listed fall back to their name with underscores turned into
# spaces (naively pluralized with a trailing "s").
_FIELD_LABELS_FR = {"code_disponible_sur": ("lien de dépôt", "liens de dépôt")}


@dataclass
class PipelineResult:
    new_data: list[dict]
    diff: dict
    should_commit: bool
    abort_reason: str | None
    changelog_entry: dict | None = field(default=None)


def write_output(result: PipelineResult, data_path: Path, changelog_path: Path) -> None:
    """Writes data.json (full replace) and appends one entry to changelog.json.

    Shared by the fixture-based and live-crawl entrypoints so the output
    format only needs to change in one place.
    """
    data_path.write_text(json.dumps(result.new_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    changelog = json.loads(changelog_path.read_text(encoding="utf-8")) if changelog_path.exists() else []
    changelog.append(result.changelog_entry)
    changelog_path.write_text(json.dumps(changelog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class RunOutcome:
    message: str
    exit_code: int


def describe_and_maybe_write(
    result: PipelineResult, data_path: Path, changelog_path: Path, dry_run: bool
) -> RunOutcome:
    """Decides what to do with a PipelineResult and, unless dry_run, does it.

    Pulled out of scripts/run_live.py so this decision logic (should we
    write? what do we report?) is testable against fixture-derived results
    without touching the live site or the real filesystem paths.
    """
    if not result.should_commit:
        if result.abort_reason:
            return RunOutcome(message=f"ABORTED — no files written. Reason: {result.abort_reason}", exit_code=1)
        return RunOutcome(message="No real changes detected — nothing to commit.", exit_code=0)

    summary = result.changelog_entry["summary"]
    if dry_run:
        return RunOutcome(
            message=f"Would commit: {summary}\n{json.dumps(result.diff, ensure_ascii=False, indent=2)}",
            exit_code=0,
        )

    write_output(result, data_path, changelog_path)
    return RunOutcome(
        message=(
            f"Committed: {summary}\n"
            f"Wrote {len(result.new_data)} records to {data_path}\n"
            f"Wrote 1 changelog entry to {changelog_path}"
        ),
        exit_code=0,
    )


def _group_slugs_by_repo(records: list[dict]) -> dict[str, list[str]]:
    by_repo: dict[str, list[str]] = {}
    for record in records:
        repo = record["code_disponible_sur"]
        if repo:
            by_repo.setdefault(repo, []).append(record["slug"])
    return by_repo


def _compute_related_to(records: list[dict]) -> None:
    """Sets related_to on each record: other slugs sharing the same repo URL."""
    by_repo = _group_slugs_by_repo(records)
    for record in records:
        siblings = by_repo.get(record["code_disponible_sur"], [])
        record["related_to"] = [slug for slug in siblings if slug != record["slug"]]


def _diff_fields(slug: str, old_record: dict, new_record: dict) -> list[dict]:
    return [
        {
            "slug": slug,
            "field": field_name,
            "old": old_record.get(field_name),
            "new": new_record.get(field_name),
        }
        for field_name in _COMPARABLE_FIELDS
        if old_record.get(field_name) != new_record.get(field_name)
    ]


def _compute_diff(previous_data: list[dict], new_records: list[dict]) -> dict:
    prev_by_slug = {r["slug"]: r for r in previous_data}
    new_by_slug = {r["slug"]: r for r in new_records}
    prev_slugs = set(prev_by_slug)
    new_slugs = set(new_by_slug)

    gone = prev_slugs - new_slugs
    appeared = new_slugs - prev_slugs
    common = prev_slugs & new_slugs

    # Rename detection: pair a disappeared slug with an appeared slug only
    # when exactly one of each shares the same code_disponible_sur — an
    # unambiguous 1:1 match. Anything more tangled (e.g. two disappeared
    # slugs sharing a repo with two appeared ones) is left as separate
    # added/removed entries rather than guessing a pairing.
    gone_by_repo = _group_slugs_by_repo([prev_by_slug[slug] for slug in gone])
    appeared_by_repo = _group_slugs_by_repo([new_by_slug[slug] for slug in appeared])

    renamed = []
    renamed_old_slugs: set[str] = set()
    renamed_new_slugs: set[str] = set()
    for repo, old_slugs in gone_by_repo.items():
        new_slugs_for_repo = appeared_by_repo.get(repo, [])
        if len(old_slugs) == 1 and len(new_slugs_for_repo) == 1:
            renamed.append({"old_slug": old_slugs[0], "new_slug": new_slugs_for_repo[0]})
            renamed_old_slugs.add(old_slugs[0])
            renamed_new_slugs.add(new_slugs_for_repo[0])

    changed = []
    for slug in sorted(common):
        changed.extend(_diff_fields(slug, prev_by_slug[slug], new_by_slug[slug]))
    # A renamed pair is the same project under a new slug — its other
    # fields can still have changed in the same run, so diff those too
    # (reported under the new slug) instead of only reporting the rename.
    for entry in renamed:
        changed.extend(_diff_fields(entry["new_slug"], prev_by_slug[entry["old_slug"]], new_by_slug[entry["new_slug"]]))

    return {
        "added": sorted(appeared - renamed_new_slugs),
        "removed": sorted(gone - renamed_old_slugs),
        "changed": changed,
        "renamed": renamed,
    }


def _check_thresholds(previous_data: list[dict], new_records: list[dict]) -> str | None:
    if previous_data and len(new_records) < len(previous_data):
        return f"Project count dropped from {len(previous_data)} to {len(new_records)}"

    if new_records:
        missing = sum(1 for r in new_records if any(not r.get(f) for f in _REQUIRED_FIELDS))
        ratio = missing / len(new_records)
        if ratio > _MISSING_FIELD_ABORT_RATIO:
            return (
                f"{missing}/{len(new_records)} rows ({ratio:.0%}) are missing a required "
                f"field (titre, slug, or code_disponible_sur) — exceeds the "
                f"{_MISSING_FIELD_ABORT_RATIO:.0%} threshold"
            )

    return None


def _summarize(diff: dict) -> str:
    parts = []

    if diff["added"]:
        n = len(diff["added"])
        parts.append(f"{n} nouveau{'x' if n > 1 else ''} projet{'s' if n > 1 else ''}")
    if diff["removed"]:
        n = len(diff["removed"])
        parts.append(f"{n} projet{'s' if n > 1 else ''} retiré{'s' if n > 1 else ''}")
    if diff["renamed"]:
        n = len(diff["renamed"])
        parts.append(f"{n} renommage{'s' if n > 1 else ''}")
    if diff["changed"]:
        by_field: dict[str, int] = {}
        for entry in diff["changed"]:
            by_field[entry["field"]] = by_field.get(entry["field"], 0) + 1
        for field_name, n in by_field.items():
            generic = field_name.replace("_", " ")
            singular, plural = _FIELD_LABELS_FR.get(field_name, (generic, generic + "s"))
            parts.append(f"{n} {singular if n == 1 else plural} mis à jour")

    return ", ".join(parts) if parts else "Aucun changement"


def run_pipeline(html_pages: dict[str, str], previous_data: list[dict]) -> PipelineResult:
    now = datetime.now(timezone.utc).isoformat()
    records = [parse_detail_page(html, url) for url, html in html_pages.items()]
    for record in records:
        record["last_checked"] = now
    _compute_related_to(records)

    diff = _compute_diff(previous_data, records)
    abort_reason = _check_thresholds(previous_data, records)

    if abort_reason:
        return PipelineResult(new_data=records, diff=diff, should_commit=False, abort_reason=abort_reason)

    has_real_changes = any(diff[key] for key in ("added", "removed", "changed", "renamed"))
    if not has_real_changes:
        return PipelineResult(new_data=records, diff=diff, should_commit=False, abort_reason=None)

    changelog_entry = {"date": now, "summary": _summarize(diff), **diff}
    return PipelineResult(new_data=records, diff=diff, should_commit=True, abort_reason=None, changelog_entry=changelog_entry)
