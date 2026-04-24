# LLM-Wiki Schema (Phase 1)

This file is the schema-layer contract for how the wiki is maintained.

## Layer Model

- `raw/`: immutable source materials.
- `wiki/`: compiled markdown knowledge base.
- `schema/`: conventions and workflows that govern ingest, query, and lint behavior.

## Required Note Frontmatter

Each note in `wiki/` must include:

- `id`
- `title`
- `type`
- `created`
- `updated`
- `sources`

Optional:

- `tags`
- `status`
- `aliases`
- `related`

## Ingest Rules

- Ingest copies source files into `raw/`.
- Ingest creates/updates a note in `wiki/`.
- Default ingest writes `## Summary`.
- Ingest updates `wiki/index.md` and appends `wiki/log.md`.
- Optional flags:
  - `--no-summarize`
  - `--link-suggestions`
  - `--touch-related`

## Query Rules

- `query` answers are synthesized from existing wiki notes.
- Answers must include source citations.
- `query --save` writes the answer back to `wiki/` as a `query-*` note.

## Lint Rules

- `check` enforces structural validity.
- `lint` runs check-like validation plus health warnings (orphan notes, missing summaries).

## Phase 1 Constraints

- Markdown in `wiki/` is canonical source of truth.
- No database is required.
- No vector search, pgvector, knowledge graph, or agent memory in Phase 1 **core** implementation.

## Optional derived graph (Graphify)

Graphify (external tool + Codex skill under `.agents/skills/graphify/`) may produce a **rebuildable** knowledge graph under **`work/graphify-out/`** when the agent runs the pipeline from **`work/`** (so `graphify-out/` resolves there).

- **Non-authoritative:** `graph.json`, `GRAPH_REPORT.md`, HTML exports, and any Graphify `wiki/` subtree are **not** canonical. They are for navigation, relationship discovery, and suggested questions.
- **Citations:** Factual claims in project notes still cite `raw/` and curated `wiki/` pages per the rules above.
- **Isolation:** Do not merge Graphify-generated markdown into the top-level **`wiki/`** without a human editorial pass.
