// normalizeProject(record) maps one canonical data.json record (full field
// names) into the internal shape render()/matches()/countFor()/cardHTML()
// already expect (short keys, from the original hardcoded DATA array).
// Loadable both as a plain <script> in the browser and via require() in
// Node tests — no bundler, consistent with the site's no-build-step design.
function normalizeProject(record) {
  return {
    t: record.titre || "",
    u: record.slug || "",
    a: record.type_auteur || "",
    o: record.objectif || [],
    d: record.domaine_medical || [],
    l: record.langage || [],
    dt: record.donnees_application || [],
    v: record.validation || "",
    m: record.maintenance || "",
    repo: record.code_disponible_sur || "",
    lastChecked: record.last_checked || "",
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { normalizeProject };
}
