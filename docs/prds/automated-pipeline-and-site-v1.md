# PRD: Automated weekly BOAS catalogue pipeline + data-driven site v1

> **Status**: drafted, not yet published to an issue tracker — this repo has
> no GitHub remote yet (see `docs/agents/issue-tracker.md`). Once the repo
> exists, publish this as a GitHub issue and apply the `ready-for-agent`
> label (per `docs/agents/triage-labels.md`), then delete this file (its
> content becomes the issue body).
>
> Synthesized from `DECISIONS.md` (2026-07-07 design session), cross-checked
> against `PROJECT_GOAL.md`, `CONTEXT.md`, and the current `site/index.html`
> and `data/*.csv`.

## Problem Statement

The official BOAS catalogue page is confusing to browse (poorly named
facets, no overview, overlapping categories), which is why an unofficial
mirror was worth building in the first place. But the mirror as it exists
today (`site/index.html`) has its own problem: its dataset is a hand-curated
JS array that was originally produced from memory and only partially
re-verified against the live site, field by field. It will silently drift
out of date the moment the official catalogue adds a project, removes one,
or changes a field — nobody is re-checking it. Separately, there are two
different manually-produced data sources in this repo (`site/index.html`'s
`DATA` array and `data/boas_extraction_brute.csv`) that disagree on schema
and have never been reconciled, so neither can be trusted as a definitive
answer to "what does the official catalogue say right now."

## Solution

Replace the hand-maintained dataset with a weekly automated pipeline that
fetches the live official catalogue, parses it into one canonical schema,
diffs it against the last known-good version committed in this repo, and
commits only real changes — never a silent, unreviewed bad write. The site
switches from a hardcoded data array to loading this versioned `data.json`
at runtime, with no functional change to browsing/filtering in this first
version. The two existing hand-built data sources are retired once the
pipeline's first live scrape is verified to at least match their coverage.

## User Stories

1. As a catalogue consumer, I want the list of projects to reflect what's
   currently on the official HDH site, so that I don't act on stale
   information.
2. As a catalogue consumer, I want to see when a project's data was last
   confirmed against the official page, so that I can judge how fresh it is.
3. As a catalogue consumer, I want every project's actual code repository
   link, regardless of whether it's hosted on GitLab, GitHub, or an
   institution's own GitLab instance, so that I can find the real code
   instead of being misled by the official site's "Gitlab" label.
4. As a catalogue consumer, I want a direct link to each project's official
   HDH page instead of a paraphrased summary baked into this site, so that I
   always see the authoritative, up-to-date description.
5. As a catalogue consumer, I want to keep filtering by domain médical,
   langage, données d'application, validation, maintenance, and type
   d'auteur exactly as I can today, so that the switch to live data doesn't
   regress the tool I already use.
6. As a catalogue consumer, I want the derived "type de fiche" facet (Data
   challenge / Requête-type / Algorithme) to keep working, so that this
   site's one advantage over the official page is preserved.
7. As a catalogue consumer, I want known duplicate/near-duplicate listings
   (e.g. "Top Diabète" and "Cartographie G12", which share a repo) visually
   grouped, so that I understand they're the same underlying tool without
   the catalogue silently merging or hiding either official entry.
8. As a catalogue consumer, I want the search bar and facet counts to behave
   identically to today, so that my existing habits transfer.
9. As the project maintainer, I want the catalogue refreshed automatically
   every week without my manual involvement, so that maintenance cost stays
   near zero.
10. As the project maintainer, I want the pipeline to detect brand-new
    projects on the official site automatically (via listing-page pagination),
    rather than depending on a hardcoded list of slugs, so that new HDH
    catalogue entries are never silently missed.
11. As the project maintainer, I want the pipeline to abort — without
    committing anything — if the total project count drops at all, or if a
    required field is empty/unparsable on more than 10% of rows, so that a
    transient scrape glitch or an official site redesign never corrupts the
    published dataset.
12. As the project maintainer, I want repeated pipeline failures to reuse a
    single labeled GitHub issue instead of opening a new one every week, so
    that I'm not spammed and can see failure history in one place.
13. As the project maintainer, I want that failure issue to close
    automatically on the next successful run, so that I don't have to
    manually track resolution.
14. As the project maintainer, I want every automated commit to have a
    specific, human-readable message (e.g. "3 nouveaux projets, 1 lien de
    dépôt mis à jour"), so that `git log` alone tells me what changed each
    week without opening a diff.
15. As the project maintainer, I want a structured `changelog.json` updated
    on every successful run, so that a future "historique des changements"
    UI doesn't depend on parsing git history or calling the GitHub API from
    a static site.
16. As the project maintainer, I want a slug that disappears and a new slug
    that appears in the same run, both pointing at the same
    `code_disponible_sur`, treated as a rename (one changed field) rather
    than a delete + an add, so that the changelog and history stay
    meaningful across title changes on the source site.
17. As the project maintainer, I want committed HTML fixtures (listing page
    + a few detail pages) in the repo, so that I can develop and test the
    parser offline without hitting the live site on every iteration.
18. As the project maintainer, I want a dry-run mode for the pipeline, so
    that I can preview what a run would change before it's ever wired to
    auto-commit.
19. As the project maintainer, I want the first pipeline run to fully
    replace the two existing hand-built sources rather than trying to
    reconcile them field-by-field, so that I'm not stuck hand-merging two
    already-known-to-be-inconsistent datasets.
20. As the project maintainer, I want the old CSVs deleted only after the
    new `data.json` is verified equivalent/sufficient, so that I don't lose
    the only record of the manual extraction work before it's confirmed
    unnecessary.
21. As a future contributor reading this repo, I want the parser to key off
    the stable Markdown/HTML section headings on each detail page
    (Objectifs, Auteur(s), Domaine médical, …) rather than fragile CSS
    selectors, so that small official-site styling changes don't break
    scraping.
22. As a future contributor, I want the taxonomy fields (Objectif, Domaine
    médical, Langage, Données d'application, Validation, Maintenance) parsed
    as closed official vocabularies rather than classified/summarized, so
    that the scraper needs no NLP or fuzzy matching for these fields — just
    deterministic parsing.
23. As the project maintainer, I want the crawl to run at a low, clearly
    identified rate (weekly, one client, real user-agent), so that it
    stays within what `robots.txt` and normal politeness allow.
24. As a catalogue consumer, I want the site to keep loading correctly if
    `data.json` briefly fails to fetch, so that a bad network moment doesn't
    show a broken, empty page with no explanation.

## Implementation Decisions

### Scraper (Python)

- Language/stack: Python with `requests`/`httpx` for HTTP and an HTML parser
  (e.g. BeautifulSoup or lxml — no specific library was mandated in
  `DECISIONS.md`; either is fine as long as parsing keys off section
  headings, not CSS selectors, per the known-quirks note in `CLAUDE.md`).
- Core seam — a single pure function, no network/git/GitHub-API access
  inside it:

  ```
  run_pipeline(html_pages: dict[url, html], previous_data: list[ProjectRecord]) -> PipelineResult

  PipelineResult:
    new_data: list[ProjectRecord]
    diff: { added: [...], removed: [...], changed: [{slug, field, old, new}, ...], renamed: [{old_slug, new_slug}, ...] }
    should_commit: bool
    abort_reason: str | None       # set when should_commit is False
    changelog_entry: ChangelogEntry | None   # set when should_commit is True
  ```

  (Schema sketched here to pin down the decision precisely; not from a
  running prototype.)
- Thin adapters around `run_pipeline`, each doing exactly one IO
  responsibility and nothing else: (a) fetch listing pages `?page=0..N` and
  every detail page they link to, (b) read `data.json` from the repo as
  `previous_data`, (c) on `should_commit == True`, write `data.json` +
  append to `changelog.json` + `git commit` + `git push` to `main`, (d) on
  `should_commit == False`, open-or-reuse the `scraper-failure`-labeled
  GitHub issue with `abort_reason` in the body, leaving existing data
  untouched, (e) on success after a prior failure, close that issue.
- Abort thresholds (exact, from `DECISIONS.md`): any drop in total project
  count (even by one), OR a required field (title, slug, repo URL) empty or
  unparsable on more than 10% of rows.
- Identity/dedup: slug is the primary key. Same-run slug disappearance +
  appearance pointing at the same `code_disponible_sur` = rename (single
  field changed), not delete+add. `related_to` is computed every run via
  exact match on `code_disponible_sur` across *different* slugs (for known
  cases like Top Diabète / Cartographie G12) — this is calculated fresh
  each run, not hand-maintained.
- Scheduling: GitHub Actions cron, weekly, early Monday UTC.
- Fixtures: real HTML pages (the listing page + at least the
  `ehden-persephone` detail page already fetched during the design session)
  committed under a test-fixtures location, used both for parser tests and
  for a dry-run mode that runs `run_pipeline` against fixtures instead of
  live HTML.

### Canonical schema

Union of the two existing sources, simplified (per `DECISIONS.md`):
taxonomy fields (closed official vocabularies — Objectif, Domaine médical,
Langage, Données d'application, Validation, Maintenance), `slug` (primary
key), `code_disponible_sur` (repo URL), `url_fiche_boas_source` (official
page URL), `last_checked` (timestamp, replaces `statut_extraction`/`source`
— every row is reconfirmed live every week so provenance/confidence tracking
no longer applies), `related_to` (computed, see above). Explicitly dropped:
`statut_extraction`, `source`, `resume_technique_paraphrase` (no free-text
summary field — link to the official page instead).

### Bootstrap and migration

- First pipeline run = a full live scrape of all ~48 current listings,
  becoming the initial `data.json`. Neither `site/index.html`'s `DATA` array
  nor the existing CSVs are used as input to this bootstrap — they are
  superseded, not manually reconciled.
- `data/boas_extraction_brute.csv` and `data/boas_fetch_log.csv` are deleted
  once `data.json` is verified equivalent/sufficient. Git history keeps them
  accessible.

### Site v1 (frontend)

- Functionally unchanged from today's prototype (facets, search, cards) —
  the only change is loading `data.json` at runtime instead of the
  hardcoded `DATA` array.
- New seam: a pure `normalizeProject(record)` function that maps one
  `data.json` record (new canonical schema, full field names) into the
  internal shape `render()`/`matches()`/`countFor()`/`cardHTML()` already
  consume (today's `t`/`u`/`a`/`o`/`d`/`l`/`dt`/`v`/`m` + computed `kind` +
  `href`). This keeps the existing rendering code untouched and isolates
  the schema translation in one testable place.
- `kindOf()` (the derived "type de fiche" facet) keeps running client-side
  against the title, same as today — it's not part of the canonical schema
  computed server-side, no decision to change that in `DECISIONS.md`.
- Fetch-failure handling: if `data.json` fails to load, show an explanatory
  empty/error state rather than a blank page (implementation detail, not
  specified in `DECISIONS.md` — flagged as an assumption, see Further Notes).
- Deployment: GitHub Pages, "deploy from branch" on `main`, `/site` folder —
  no dedicated Actions deploy workflow (consistent with no frontend build
  step).

## Testing Decisions

- Test external behavior, not internals: assert on `run_pipeline()`'s
  returned `PipelineResult` (new dataset, diff, should_commit, abort_reason,
  changelog_entry) given fixture HTML inputs — not on intermediate parsing
  helper calls.
- `run_pipeline()` is the primary unit-under-test for the backend: cover at
  least (a) a clean run with no changes, (b) a new project appearing, (c) a
  project disappearing (should abort), (d) a field changing on an existing
  project, (e) a slug rename via matching `code_disponible_sur`, (f) more
  than 10% of rows missing a required field (should abort), (g) the
  `related_to` computation across two known-duplicate fixture entries.
  Fetching (network) and git/GitHub-API calls (the thin adapters) are not
  unit tested — cover them, if at all, with a thin integration/smoke test
  separate from the pure-function suite.
- `normalizeProject()` is the primary unit-under-test for the frontend:
  cover mapping a full `data.json`-shaped record into the existing render
  shape, including a record missing optional taxonomy fields (should
  produce the same "Non renseigné"/empty-array fallbacks the current
  `valuesOf()` already handles).
- Prior art: none — this repo has no existing test setup, framework, or
  test directory of any kind. The implementer should pick the lightest
  option that fits each language (e.g. `pytest` for the Python pipeline;
  for the frontend, given there's no build step or package.json today,
  either Node's built-in `node:test` run against the extracted
  `normalizeProject()` function, or a small assertion script — avoid
  introducing a bundler/build step solely for tests, since that would
  contradict the site's no-build-step design).

## Out of Scope

- Sort options, CSV/JSON export, and an in-UI changelog page — explicitly
  deferred to v2+ in `DECISIONS.md`, even though the underlying
  `changelog.json` data exists from day one.
- Formalizing the "official label → reformulated label" mapping (currently
  implicit in `site/index.html`'s facet labels) as a separate config file —
  flagged as still open in `DECISIONS.md`, not part of this PRD.
- Actually creating the git repository and GitHub remote. `DECISIONS.md`
  records the decision to make it a public GitHub repo but deliberately
  left the timing to the execution step — this is a prerequisite for
  deploying the pipeline (Actions, issue reuse, Pages) but is infrastructure
  setup, not part of this feature's implementation.
- A relational database or server backend (explicitly out of scope
  project-wide, per `CLAUDE.md`).
- Republishing verbatim official-page text (explicitly out of scope
  project-wide, per `CLAUDE.md` — this PRD's removal of the paraphrased
  summary field in favor of a direct link reinforces this, it doesn't
  relax it).
- Scraper implementation details beyond what's specified here (retry
  strategy on transient network errors, exact HTTP client config) —
  `DECISIONS.md` explicitly left these to the build stage; treat "any
  fetch failure aborts the run via the existing failure-issue mechanism, no
  bespoke retry logic" as a reasonable default unless the implementer finds
  a reason otherwise.

## Further Notes

- The `related_to` computation and the slug-rename detection both depend on
  `code_disponible_sur` being a reliable join key. Per `CLAUDE.md`'s known
  quirks, this field is trustworthy (it's the actual `href`, not the
  unreliable "Gitlab" label) — no extra normalization should be needed
  beyond exact string match, but worth a fixture case if a trailing-slash or
  `.git`-suffix inconsistency ever shows up in practice.
- The empty/error state for a failed `data.json` fetch (see Site v1,
  Implementation Decisions) is an assumption filled in by this PRD, not an
  explicit `DECISIONS.md` ruling — confirm with the maintainer if a
  specific UX is wanted here, otherwise a minimal "Impossible de charger le
  catalogue, réessayez plus tard" message is enough for v1.
