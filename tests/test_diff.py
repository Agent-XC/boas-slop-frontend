from conftest import load_fixture

from pipeline.core import run_pipeline

EHDEN_URL = "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/ehden-persephone"
TOP_DIABETE_URL = (
    "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/"
    "algorithme-pour-construire-le-top-diabete-de-la-cartographie"
)
CARTOGRAPHIE_G12_URL = (
    "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/"
    "cartographie-des-pathologies-et-des-depenses-version-g12"
)


def _previous_record(**overrides):
    base = {
        "slug": "placeholder",
        "titre": "Placeholder",
        "type_auteur": "Agence",
        "objectif": ["Autre"],
        "domaine_medical": ["Autre"],
        "langage": ["Python"],
        "donnees_application": ["Autre"],
        "validation": "Validé",
        "maintenance": "Ad-hoc",
        "code_disponible_sur": "https://example.test/repo",
        "url_fiche_boas_source": "https://example.test/fiche",
        "last_checked": "2020-01-01T00:00:00+00:00",
        "related_to": [],
    }
    base.update(overrides)
    return base


def test_classifies_added_changed_and_renamed_and_commits():
    previous_data = [
        _previous_record(
            slug="ehden-persephone",
            titre="EHDEN / Persephone",
            code_disponible_sur="https://gitlab.com/healthdatahub/applications-du-hdh/snds_omop",
            validation="Non validé",  # differs from the fixture's "Validé" -> changed
        ),
        _previous_record(
            slug="old-slug-for-top-diabete",
            titre="Old title for top diabète",
            code_disponible_sur="https://gitlab.com/healthdatahub/boas/cnam/top-diabete",  # same repo as the new fixture
        ),
    ]
    html_pages = {
        EHDEN_URL: load_fixture("detail_ehden-persephone.html"),
        TOP_DIABETE_URL: load_fixture("detail_top-diabete.html"),
        CARTOGRAPHIE_G12_URL: load_fixture("detail_cartographie-g12.html"),  # brand new, no prior match
    }

    result = run_pipeline(html_pages, previous_data)

    assert result.diff["added"] == ["cartographie-des-pathologies-et-des-depenses-version-g12"]
    assert result.diff["removed"] == []
    assert result.diff["renamed"] == [
        {"old_slug": "old-slug-for-top-diabete", "new_slug": "algorithme-pour-construire-le-top-diabete-de-la-cartographie"}
    ]
    assert {"slug": "ehden-persephone", "field": "validation", "old": "Non validé", "new": "Validé"} in result.diff["changed"]

    assert result.should_commit is True
    assert result.abort_reason is None
    assert result.changelog_entry is not None
    assert result.changelog_entry["added"] == result.diff["added"]
    assert "nouveau" in result.changelog_entry["summary"]
    assert "renommage" in result.changelog_entry["summary"]


def test_removed_project_triggers_count_drop_abort_without_writing():
    previous_data = [
        _previous_record(
            slug="ehden-persephone",
            titre="EHDEN / Persephone",
            code_disponible_sur="https://gitlab.com/healthdatahub/applications-du-hdh/snds_omop",
            validation="Validé",
        ),
        _previous_record(slug="truly-gone-project", code_disponible_sur="https://example.test/gone-repo"),
    ]
    html_pages = {EHDEN_URL: load_fixture("detail_ehden-persephone.html")}

    result = run_pipeline(html_pages, previous_data)

    assert result.diff["removed"] == ["truly-gone-project"]
    assert result.should_commit is False
    assert result.abort_reason is not None
    assert "2" in result.abort_reason and "1" in result.abort_reason
    assert result.changelog_entry is None


def test_missing_required_field_ratio_triggers_abort():
    good_url = EHDEN_URL
    bad_url = "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/broken-page"
    broken_html = "<html><body><p>No heading, no repo link here.</p></body></html>"

    html_pages = {good_url: load_fixture("detail_ehden-persephone.html"), bad_url: broken_html}

    result = run_pipeline(html_pages, previous_data=[])

    assert result.should_commit is False
    assert result.abort_reason is not None
    assert result.changelog_entry is None


def test_related_to_recomputed_fresh_with_nonempty_previous_data():
    previous_data = [
        _previous_record(
            slug="synthetic-dup-a",
            code_disponible_sur="https://gitlab.com/healthdatahub/shared-repo-example",
            related_to=[],  # stale: this run should recompute it, not trust the old value
        )
    ]
    html_pages = {
        "https://example.test/synthetic-dup-a": load_fixture("detail_synthetic-dup-a.html"),
        "https://example.test/synthetic-dup-b": load_fixture("detail_synthetic-dup-b.html"),
    }

    result = run_pipeline(html_pages, previous_data)

    by_slug = {r["slug"]: r for r in result.new_data}
    assert by_slug["synthetic-dup-a"]["related_to"] == ["synthetic-dup-b"]
    assert by_slug["synthetic-dup-b"]["related_to"] == ["synthetic-dup-a"]
    assert result.diff["added"] == ["synthetic-dup-b"]
    assert result.should_commit is True


def test_renamed_project_with_other_field_changes_reports_both():
    # top-diabete's real fixture validation is "Non validé" (confirmed via
    # live fetch) — set the previous record's validation to "Validé" so a
    # rename and a field change happen on the same pair in the same run.
    previous_data = [
        _previous_record(
            slug="old-slug-for-top-diabete",
            code_disponible_sur="https://gitlab.com/healthdatahub/boas/cnam/top-diabete",
            validation="Validé",
        ),
    ]
    html_pages = {TOP_DIABETE_URL: load_fixture("detail_top-diabete.html")}

    result = run_pipeline(html_pages, previous_data)

    new_slug = "algorithme-pour-construire-le-top-diabete-de-la-cartographie"
    assert result.diff["renamed"] == [{"old_slug": "old-slug-for-top-diabete", "new_slug": new_slug}]
    assert {"slug": new_slug, "field": "validation", "old": "Validé", "new": "Non validé"} in result.diff["changed"]
    assert result.should_commit is True
    assert "renommage" in result.changelog_entry["summary"]
    assert "validation" in result.changelog_entry["summary"]


def test_no_real_changes_results_in_no_commit_and_no_abort_reason():
    html_pages = {EHDEN_URL: load_fixture("detail_ehden-persephone.html")}
    first = run_pipeline(html_pages, previous_data=[])

    result = run_pipeline(html_pages, previous_data=first.new_data)

    assert result.diff == {"added": [], "removed": [], "changed": [], "renamed": []}
    assert result.should_commit is False
    assert result.abort_reason is None
    assert result.changelog_entry is None
