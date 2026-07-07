from conftest import load_fixture

from pipeline.core import run_pipeline

EHDEN_URL = "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/ehden-persephone"


def test_bootstrap_run_with_single_fixture_produces_one_record():
    html_pages = {EHDEN_URL: load_fixture("detail_ehden-persephone.html")}

    result = run_pipeline(html_pages, previous_data=[])

    assert len(result.new_data) == 1
    record = result.new_data[0]
    assert record["slug"] == "ehden-persephone"
    assert record["titre"] == "EHDEN / Persephone"
    assert record["domaine_medical"] == ["Autre"]
    assert record["langage"] == ["SQL"]
    assert record["validation"] == "Validé"
    assert record["donnees_application"] == ["Base principale"]
    assert record["type_auteur"] == "Plateforme de données"
    assert record["code_disponible_sur"] == "https://gitlab.com/healthdatahub/applications-du-hdh/snds_omop"
    assert record["url_fiche_boas_source"] == EHDEN_URL

    assert result.diff["added"] == ["ehden-persephone"]
    assert result.diff["removed"] == []
    assert result.diff["changed"] == []
    assert result.diff["renamed"] == []
    assert result.should_commit is True
    assert result.abort_reason is None
    assert result.changelog_entry["added"] == ["ehden-persephone"]


TOP_DIABETE_URL = (
    "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/"
    "algorithme-pour-construire-le-top-diabete-de-la-cartographie"
)
CARTOGRAPHIE_G12_URL = (
    "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/"
    "cartographie-des-pathologies-et-des-depenses-version-g12"
)
EDS_NLP_URL = (
    "https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante/"
    "eds-nlp-framework-de-nlp-modulaire-et-rapide-compatible-avec"
)


def test_bootstrap_run_with_full_fixture_set():
    html_pages = {
        EHDEN_URL: load_fixture("detail_ehden-persephone.html"),
        TOP_DIABETE_URL: load_fixture("detail_top-diabete.html"),
        CARTOGRAPHIE_G12_URL: load_fixture("detail_cartographie-g12.html"),
        EDS_NLP_URL: load_fixture("detail_eds-nlp.html"),
    }

    result = run_pipeline(html_pages, previous_data=[])

    by_slug = {record["slug"]: record for record in result.new_data}
    assert set(by_slug) == {
        "ehden-persephone",
        "algorithme-pour-construire-le-top-diabete-de-la-cartographie",
        "cartographie-des-pathologies-et-des-depenses-version-g12",
        "eds-nlp-framework-de-nlp-modulaire-et-rapide-compatible-avec",
    }

    top_diabete = by_slug["algorithme-pour-construire-le-top-diabete-de-la-cartographie"]
    assert top_diabete["type_auteur"] == "Administrations et ministère"
    assert top_diabete["langage"] == ["Python", "SAS"]

    cartographie_g12 = by_slug["cartographie-des-pathologies-et-des-depenses-version-g12"]
    assert cartographie_g12["domaine_medical"] == [
        "Cancers",
        "Maladies cardio-vasculaires",
        "Diabète",
        "Maladies neurodégénératives",
        "Santé mentale et Psychiatrie",
        "Périnatalité et Santé reproductive",
        "Maladies respiratoires",
        "Maladies infectieuses",
        "Autre",
    ]

    # Verified live: despite CLAUDE.md's known-quirks note claiming these two
    # share a repo, they currently point at two different GitLab paths, so no
    # related_to match is expected here.
    assert top_diabete["code_disponible_sur"] != cartographie_g12["code_disponible_sur"]
    assert top_diabete["related_to"] == []
    assert cartographie_g12["related_to"] == []

    eds_nlp = by_slug["eds-nlp-framework-de-nlp-modulaire-et-rapide-compatible-avec"]
    assert eds_nlp["validation"] == ""
    assert eds_nlp["code_disponible_sur"] == "https://github.com/aphp/edsnlp"


def test_related_to_matches_records_sharing_a_repo():
    html_pages = {
        "https://example.test/synthetic-dup-a": load_fixture("detail_synthetic-dup-a.html"),
        "https://example.test/synthetic-dup-b": load_fixture("detail_synthetic-dup-b.html"),
        EHDEN_URL: load_fixture("detail_ehden-persephone.html"),
    }

    result = run_pipeline(html_pages, previous_data=[])

    by_slug = {record["slug"]: record for record in result.new_data}
    assert by_slug["synthetic-dup-a"]["related_to"] == ["synthetic-dup-b"]
    assert by_slug["synthetic-dup-b"]["related_to"] == ["synthetic-dup-a"]
    assert by_slug["ehden-persephone"]["related_to"] == []
