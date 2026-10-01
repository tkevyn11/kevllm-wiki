# LLM-Wiki Schema (Phase 1)

This file is the schema-layer contract for how the wiki is maintained.

## Layer Model

- `raw/`: source copies. May be private. Do not edit files here as part of note maintenance.
- `wiki/`: canonical Markdown and YAML knowledge.
- `work/`: transient manifests and logs. Not canonical. Manifests can contain local paths.
- `derived/`: rebuildable graph, vector, semantic, and extraction outputs. Never canonical.
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

- Ingest without `--extract` copies source files into `raw/` by basename.
- Ingest without `--extract` creates a new note in `wiki/`. If that id already exists, the new note id is suffixed (`-2`, `-3`, ...) and the existing note is not rewritten.
- `llm-wiki ingest --extract` keeps relative paths under `raw/`, runs the local quality gate, and creates a wiki note only for status `clean`. Other statuses stay out of `wiki/`.
- `llm-wiki ingest --extract --ocr` runs optional local OCR for images and textless PDFs, then the same quality gate. `review` is not promoted automatically. Without `--ocr`, those files stay `ocr_needed`.
- Default ingest writes `## Summary`.
- Ingest updates `wiki/index.md` and appends `wiki/log.md`.
- Optional flags:
  - `--no-summarize`
  - `--link-suggestions`
  - `--touch-related`

## Query Rules

- `query` selects local notes by term overlap and prints their summaries with citations. It does not call an external model. Notes of type `query` are skipped.
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

Graphify (external tool + Codex skill under `.agents/skills/graphify/`) may produce a **rebuildable** knowledge graph under **`work/graphify-out/`** when the agent runs the pipeline from **`work/`**. The long-term home for that class of output is **`derived/`**. Until the skill is moved, `work/graphify-out/` stays non-canonical transient output.

- **Non-authoritative:** `graph.json`, `GRAPH_REPORT.md`, HTML exports, and any Graphify `wiki/` subtree are **not** canonical. They are for navigation, relationship discovery, and suggested questions.
- **Citations:** Factual claims in project notes still cite `raw/` and curated `wiki/` pages per the rules above.
- **Isolation:** Do not merge Graphify-generated markdown into the top-level **`wiki/`** without a human editorial pass.
