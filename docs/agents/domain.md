# Domain docs

## Layout: single-context

This repo has one `CONTEXT.md` at the repo root — there is no `CONTEXT-MAP.md`
and no per-subdirectory contexts. Skills that read domain docs (e.g.
`improve-codebase-architecture`, `diagnosing-bugs`, `tdd`) should read
`CONTEXT.md` directly rather than looking for a context map.

## Architectural decisions: `DECISIONS.md`, not `docs/adr/`

This repo does **not** use a `docs/adr/` directory. Design and architecture
decisions are instead recorded in a single root-level `DECISIONS.md`, written
as a narrative log of design/"grilling" sessions (each session dated, with a
"facts verified" section separated from "decisions made"). Skills that would
normally read individual ADR files under `docs/adr/` should read
`DECISIONS.md` instead — treat each dated section as one ADR-equivalent.

## Other root-level docs worth knowing about

- `PROJECT_GOAL.md` — the original project brief (what's wanted, in French).
  Read this before `CONTEXT.md`.
- `CONTEXT.md` — status log: what's been built, what's solid vs. unverified,
  known data-quality caveats.
- `CLAUDE.md` — operational guidance for Claude Code in this repo; it already
  instructs readers to check `PROJECT_GOAL.md`, `CONTEXT.md`, and
  `DECISIONS.md` before nontrivial work. Domain-doc-reading skills should
  follow that same reading order: `PROJECT_GOAL.md` → `CONTEXT.md` →
  `DECISIONS.md`.
