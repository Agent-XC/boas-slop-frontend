const test = require("node:test");
const assert = require("node:assert/strict");
const { normalizeProject } = require("./normalize.js");

test("maps a full record into the internal card/facet shape", () => {
  const record = {
    slug: "ehden-persephone",
    titre: "EHDEN / Persephone",
    type_auteur: "Plateforme de données",
    objectif: ["Transformation de données"],
    domaine_medical: ["Autre"],
    langage: ["SQL"],
    donnees_application: ["Base principale"],
    validation: "Validé",
    maintenance: "Ad-hoc",
    code_disponible_sur: "https://gitlab.com/healthdatahub/applications-du-hdh/snds_omop",
    last_checked: "2026-07-07T19:23:47.191374+00:00",
    related_to: [],
  };

  assert.deepEqual(normalizeProject(record), {
    t: "EHDEN / Persephone",
    u: "ehden-persephone",
    a: "Plateforme de données",
    o: ["Transformation de données"],
    d: ["Autre"],
    l: ["SQL"],
    dt: ["Base principale"],
    v: "Validé",
    m: "Ad-hoc",
    repo: "https://gitlab.com/healthdatahub/applications-du-hdh/snds_omop",
    lastChecked: "2026-07-07T19:23:47.191374+00:00",
  });
});

test("falls back to empty arrays/strings for missing optional taxonomy fields", () => {
  const record = {
    slug: "eds-nlp",
    titre: "EDS-NLP",
    type_auteur: "Établissement de santé",
    // domaine_medical, langage, donnees_application, validation, maintenance
    // all omitted entirely (not just empty) — as could happen if a detail
    // page has no parseable section for a given field.
    code_disponible_sur: "https://github.com/aphp/edsnlp",
    last_checked: "2026-07-07T19:23:47.191374+00:00",
  };

  const result = normalizeProject(record);

  assert.deepEqual(result.d, []);
  assert.deepEqual(result.l, []);
  assert.deepEqual(result.dt, []);
  assert.equal(result.v, "");
  assert.equal(result.m, "");
});
