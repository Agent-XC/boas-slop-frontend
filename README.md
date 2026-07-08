# BOAS — Bibliothèque Ouverte d'Algorithmes en Santé (miroir non-officiel)

An unofficial, independently maintained catalogue of the ~48 health-data
algorithms/tools/data-challenges published by the French Health Data Hub
(HDH) in its
[Bibliothèque Ouverte d'Algorithmes en Santé](https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante).

**Live site:** https://agent-xc.github.io/boas-slop-frontend/

This project is **not affiliated with the
Plateforme des données de santé (formerly Health Data Hub).** It re-presents publicly available
catalogue metadata with clearer, recombinable facets, a single searchable
page, and one added facet the official site doesn't offer ("type de
fiche" — Data challenge / Requête-type / Algorithme).

## How it works

A pipeline periodically crawls the official catalogue, parses each
listing into a canonical schema, and writes the result to
[`site/data.json`](site/data.json), which the static site
([`site/index.html`](site/index.html)) loads at runtime — no data is
hardcoded into the page. Data and presentation are kept strictly separate.

This is being built incrementally as a sequence of GitHub issues under the
umbrella issue
[#1](https://github.com/Agent-XC/boas-slop-frontend/issues/1); see that
issue and its linked sub-issues for current status. `DECISIONS.md` records
the design decisions behind the schema, dedup/rename strategy, and pipeline
behavior.

## Repository layout

- `site/` — the static frontend (deployed to GitHub Pages via
  `.github/workflows/deploy-pages.yml`): `index.html`, the generated
  `data.json` / `changelog.json`, and `normalize.js` (maps a `data.json`
  record into the shape the page's rendering code expects).
- `pipeline/` — the scraper/pipeline core (Python): fetching
  (`fetch.py`), parsing (`parse.py`), and the diff/write logic
  (`core.py`).
- `scripts/` — entrypoints: `bootstrap_fixtures.py` runs the pipeline
  offline against the committed HTML fixtures (for parser development
  without hitting the live site); `run_live.py` runs it against the real
  catalogue.
- `tests/` — pytest suite, including real (and a couple of synthetic)
  HTML fixtures under `tests/fixtures/`.
- `data/` — raw CSVs from an earlier, manual data-collection pass,
  scheduled to be retired once the live pipeline's output is verified
  equivalent (see the umbrella issue's bootstrap/migration step).
- `docs/agents/` — configuration consumed by AI coding-agent skills used
  on this repo (issue tracker, triage labels, domain-doc layout).
- `PROJECT_GOAL.md`, `CONTEXT.md`, `DECISIONS.md`, `CLAUDE.md` — project
  brief, status log, design-decision record, and agent operating notes,
  respectively. Worth reading before making nontrivial changes.

## Development

Requires Python 3.11+ and Node.js (Node only for the frontend's tests —
nothing Node-based ships to the deployed site).

```bash
pip install -r requirements.txt

# run the Python pipeline test suite
pytest

# run the frontend's tests
node --test site/normalize.test.js

# regenerate site/data.json from committed fixtures (no network)
python scripts/bootstrap_fixtures.py

# regenerate site/data.json from a live crawl of the real catalogue
python scripts/run_live.py

# serve the site locally
cd site && python3 -m http.server 8000
```

## License

[MIT](LICENSE).
