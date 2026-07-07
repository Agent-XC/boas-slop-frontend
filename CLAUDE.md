# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

An unofficial, independently maintained catalogue of projects listed in the
**BOAS** (Bibliothèque Ouverte d'Algorithmes en Santé), a catalogue of ~48
health-data algorithms/tools/data-challenges published by the French Health
Data Hub (HDH) at
https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante.

The official page is considered confusing (poorly named facets, no overview,
overlapping categories). The end goal (not yet built) is a GitHub repo that:
1. Fetches the official catalogue automatically on a weekly cron (GitHub Actions).
2. Diffs the fetch against a versioned JSON/CSV database in the repo.
3. Updates that database only on real changes (new/removed project, changed field).
4. Serves the database through a static site (evolving `site/index.html`),
   deployed via GitHub Pages — data and presentation must be cleanly separated
   (site loads a data file at runtime; it must not have data hardcoded).

**Read `PROJECT_GOAL.md`, `CONTEXT.md`, and `DECISIONS.md` in full before
doing any nontrivial work here** — they are the authoritative project brief,
status log, and design-decision record (respectively), and much of the
reasoning below is a summary of them. `DECISIONS.md` records a 2026-07-07
design session that settled the canonical schema, identity/dedup strategy,
pipeline commit/failure/changelog behavior, bootstrap approach, and v1
frontend scope — check it before proposing architecture that revisits any
of those, and before assuming the pipeline hasn't been designed yet.

## Current state (important: read before assuming anything is "done")

There is no scraper, no build system, no tests, and no GitHub Actions yet.
This became a git repository on 2026-07-07, with a public GitHub remote at
`git@github.com:Agent-XC/boas-slop-frontend.git` (`main` branch). What exists
today:

- `site/index.html` — a standalone, dependency-free HTML/CSS/JS prototype.
  The dataset is a **hardcoded JS array** (`DATA`, in the `<script>` tag) with
  short-key fields (`t`=titre, `u`=slug, `a`=type d'auteur, `o`=objectifs,
  `d`=domaines médicaux, `l`=langages, `dt`=données d'application, `v`=validation,
  `m`=maintenance). It computes a derived, non-official facet, "type de fiche"
  (Data challenge / Requête-type / Algorithme), via `kindOf()` regex-matching
  on the title. This dataset was originally produced from memory and later
  checked page-by-page against the real site, but the per-project detail
  fields have not all been individually re-verified — see "Limites connues"
  in `CONTEXT.md`.
- `data/boas_extraction_brute.csv` — a separate, semicolon-delimited raw
  extraction table (one row per project), with different fields than
  `site/index.html`'s dataset: `titre_technique`, `chemin_gitlab`,
  `code_disponible_sur` (actual code repo URL), `organisme_porteur_gitlab`,
  `resume_technique_paraphrase` (paraphrased summary — deliberately never a
  verbatim quote, for copyright reasons), `statut_extraction` (confidence
  level — see below), `source` (extraction method), `url_fiche_boas_source`.
- `data/boas_fetch_log.csv` — a log of which official pages were actually
  fetched, by session, method of access, and whether the URL was user-supplied.

**These two data sources (the `site/index.html` DATA array and the CSVs in
`data/`) are not the same schema and have not been reconciled.** Do not treat
either as sole ground truth. Reconciling them into one canonical per-project
schema is explicit unfinished work (see PROJECT_GOAL.md's risk list).

`statut_extraction` values in the CSV, in decreasing order of trust:
- `CONFIRMÉ (page détail HDH complète)` — full official detail page read live.
- `Confirmé (GitLab)` — confirmed only via a third-party GitHub mirror
  (ecosyste.ms / data.code.gouv.fr) referencing `gitlab.com/healthdatahub/*`,
  not via the official HDH page itself. Not reliable for taxonomy fields
  (domain, validation, maintenance) since the mirror doesn't carry those.
- `PARTIELLEMENT CONFIRMÉ` — project/owner confirmed via a secondary source,
  official page and/or code repo not yet located.
- `NON CONFIRMÉ` — should be rare; verify before treating the file as final.

## Known source-catalogue quirks (don't rediscover these)

- Code repos are **not all on GitLab** despite the official site's UI always
  showing a "Gitlab" icon/label — that label is unreliable. Only the actual
  `href` of the "Lien vers le repo" button is trustworthy. Four distinct
  hosting patterns exist: `gitlab.com/healthdatahub/...` (internal HDH),
  `github.com/<org>` (external contributors: AP-HP, Epiconcept, SNDStoolers…),
  a contributor's own institutional GitLab instance off gitlab.com (e.g.
  `git.drees.fr` for DREES), and for data challenges, GitHub under the
  **challenge platform provider's** org (`drivendataorg`, `Trustii-team`) —
  never under an HDH account, and code only appears after the challenge ends.
- Each official project detail page follows a consistent
  Markdown/HTML section structure (Objectifs, Auteur(s), Domaine médical,
  Langage de programmation, Données d'application, Validation, Maintenance,
  Licence et conditions d'utilisation, Lien vers le repo) — a future scraper
  should parse on these section headings rather than on fragile CSS selectors.
- Known cross-source inconsistencies on the HDH side itself (not extraction
  errors): MORS is attributed to "GCS HUGO" in an HDH announcement article but
  to CHU de Rennes on its own official project page; EHDEN/Persephone's real
  GitLab path is `applications-du-hdh/snds_omop`, not the `boas/hdh/snds_omop`
  an earlier approximate mirror-based match suggested.
- **Correction (verified live 2026-07-07, during issue #2's implementation):**
  "Top Diabète" and "Cartographie des pathologies G12" do **not** share a
  repo — live detail pages show distinct paths
  (`boas/cnam/top-diabete` vs. `boas/cnam/cartographie-des-pathologies`).
  An earlier version of this note claimed they pointed at the same repo —
  that was wrong (likely another stale mirror-based approximation, same
  category of error as the EHDEN/Persephone case above). Don't assume
  `related_to` will match this pair.

## Before building the automated pipeline

`PROJECT_GOAL.md` originally listed 5 risks as unvalidated. The 2026-07-07
design session (`DECISIONS.md`) confirmed 3 of them directly with raw
`curl` requests (no JS rendering involved) — don't re-verify these:
- A plain HTTP client gets full HTML for both the listing page and a detail
  page (`ehden-persephone`) with no JS rendering needed.
- The listing page's raw HTML exposes `href`s to every detail page (10 per
  page) plus pagination params (`page=1` through `page=4`) — no headless
  browser required to enumerate projects.
- `robots.txt` on health-data-hub.fr has no `Disallow` covering
  `/bibliotheque-ouverte-algorithmes-sante` — nothing blocks a weekly,
  low-volume, identified-user-agent crawl.

Still open (treated as design decisions in `DECISIONS.md`, not re-testable
facts — see that file's "Ce qui reste ouvert" section):
- Slug stability across a source-side title change. Decided: the slug is
  still the primary key; if a slug disappears and a new one appears in the
  same run pointing at the same `code_disponible_sur`, treat it as a rename,
  not a delete+add.
- The canonical field schema reconciling `site/index.html` vs. `data/*.csv`.
  Decided in `DECISIONS.md`: taxonomy fields (already closed official
  vocabularies) + `code_disponible_sur` + slug + official page URL;
  `statut_extraction`/`source` dropped in favor of a `last_checked`
  timestamp; no free-text summary field.

Robustness requirements for the eventual weekly job (from PROJECT_GOAL.md,
refined with concrete thresholds in `DECISIONS.md`):
never silently commit a suspicious result — abort (no commit) if the total
project count drops at all, or if a required field (title, slug, repo URL)
is empty/unparsable on more than 10% of rows. On failure, open or reuse a
single labeled GitHub issue (e.g. `scraper-failure`) rather than one per
failed run, and close it on the next successful run; leave existing data
untouched. Keep data (`data.json`, bot-written) and presentation (static
HTML/JS, loading data at runtime) separate. Commit directly to `main` on
real changes, with specific messages (e.g. "3 nouveaux projets, 1 lien de
dépôt mis à jour"), and append a structured entry to `changelog.json` per
successful run. Provide a dry-run mode / committed HTML fixtures (e.g.
`tests/fixtures/`) so the parser can be iterated on without hitting the
live site. Cron target: weekly, early Monday UTC.

## Explicitly out of scope

- Republishing full verbatim text from official project pages — paraphrase,
  don't copy paragraphs (copyright).
- A relational database or server backend — the target is a static site
  (GitHub Pages) reading a static data file.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`Agent-XC/boas-slop-frontend`); external PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) — all five exist as real GitHub labels on the repo. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` at the repo root; architectural decisions live in `DECISIONS.md` rather than `docs/adr/`. See `docs/agents/domain.md`.
