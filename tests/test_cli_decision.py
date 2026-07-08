"""Tests for pipeline.core.describe_and_maybe_write() — the decision logic
extracted from scripts/run_live.py so it's testable against fixture data
instead of only via a manual live run.
"""

import json

from conftest import load_fixture

from pipeline.core import describe_and_maybe_write, run_pipeline

EHDEN_URL = "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/ehden-persephone"


def test_dry_run_reports_would_commit_without_writing(tmp_path):
    data_path = tmp_path / "data.json"
    changelog_path = tmp_path / "changelog.json"
    result = run_pipeline({EHDEN_URL: load_fixture("detail_ehden-persephone.html")}, previous_data=[])

    outcome = describe_and_maybe_write(result, data_path, changelog_path, dry_run=True)

    assert "Would commit" in outcome.message
    assert outcome.exit_code == 0
    assert not data_path.exists()
    assert not changelog_path.exists()


def test_real_run_with_changes_writes_and_reports_committed(tmp_path):
    data_path = tmp_path / "data.json"
    changelog_path = tmp_path / "changelog.json"
    result = run_pipeline({EHDEN_URL: load_fixture("detail_ehden-persephone.html")}, previous_data=[])

    outcome = describe_and_maybe_write(result, data_path, changelog_path, dry_run=False)

    assert "Committed" in outcome.message
    assert outcome.exit_code == 0
    assert json.loads(data_path.read_text(encoding="utf-8"))
    assert json.loads(changelog_path.read_text(encoding="utf-8"))


def test_no_real_changes_does_not_write_and_exits_zero(tmp_path):
    data_path = tmp_path / "data.json"
    changelog_path = tmp_path / "changelog.json"
    html_pages = {EHDEN_URL: load_fixture("detail_ehden-persephone.html")}
    first = run_pipeline(html_pages, previous_data=[])
    result = run_pipeline(html_pages, previous_data=first.new_data)

    outcome = describe_and_maybe_write(result, data_path, changelog_path, dry_run=False)

    assert "No real changes" in outcome.message
    assert outcome.exit_code == 0
    assert not data_path.exists()
    assert not changelog_path.exists()


def test_abort_does_not_write_and_exits_nonzero(tmp_path):
    data_path = tmp_path / "data.json"
    changelog_path = tmp_path / "changelog.json"
    previous_data = [
        {
            "slug": "gone",
            "titre": "Gone",
            "code_disponible_sur": "https://example.test/gone",
        }
    ]
    result = run_pipeline({}, previous_data=previous_data)  # everything gone -> count drop

    outcome = describe_and_maybe_write(result, data_path, changelog_path, dry_run=False)

    assert "ABORTED" in outcome.message
    assert outcome.exit_code == 1
    assert not data_path.exists()
    assert not changelog_path.exists()
