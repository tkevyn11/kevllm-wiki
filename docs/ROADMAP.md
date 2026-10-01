# Roadmap

## Guiding Principle

Phase 1 is intentionally narrow: deliver a robust local CLI workflow around markdown files. Phase 2 explores intelligence features only after Phase 1 is stable and useful.

## Phase 1: CLI LLM-Wiki Library

## Current Status

- **Current stage**: `0.2.0` release candidate on `feat/generic-framework-v0.2`. Not merged and not tagged.
- **Milestones completed**: Phase 1 milestones 1 through 6, plus the v0.2 framework work below.
- **Next stage**: owner review, then the pull request, merge, and tag. That step is separate from this candidate.

### Milestone 1: Foundation

- Status: Completed
- Create project skeleton and package layout.
- Implement `llm-wiki init` for library bootstrap.
- Standardize root folder structure (`raw/`, `wiki/`, `work/`, `docs/`).
- Generate starter `wiki/index.md` and `wiki/log.md`.

### Milestone 2: Note Model and Validation

- Status: Completed
- Implement markdown frontmatter parsing.
- Define and enforce note schema v1.
- Implement `llm-wiki check` for schema and link consistency.

### Milestone 3: Ingest Workflow

- Status: Completed
- Implement `llm-wiki ingest` for local sources.
- Store ingest manifests and processing artifacts under `work/`.
- Create or update structured notes in `wiki/` with source attribution.

### Milestone 4: Retrieval Commands

- Status: Completed
- Implement `llm-wiki list`.
- Implement `llm-wiki search` with local keyword ranking.
- Implement `llm-wiki open` for note id/path resolution.

### Milestone 5: Content Utilities

- Status: Completed
- Implement `llm-wiki link` for bidirectional note relations.
- Implement `llm-wiki summarize` with local heuristic behavior. Non-local mode exits 2.
- Implement `llm-wiki query` and `llm-wiki lint` on the same local corpus.
- Improve output formatting and command help text.

### Milestone 6: Hardening

- Status: Completed
- Add automated tests for schema, ingest, search, and checks.
- Add CLI error handling and stable exit codes.
- Finalize docs for usage and maintenance.

## v0.2.0 framework work

Status: implemented on the release-candidate branch. See [RELEASE_NOTES_v0.2.0.md](RELEASE_NOTES_v0.2.0.md).

- Quality-gated `ingest --extract` for text, Markdown, PDF, DOCX, and PPTX.
- Optional local OCR for images and scanned PDFs (`ingest --extract --ocr`).
- Explicit `review list/show/approve/reject`. `review` text stays out of `wiki/` until approval.
- Nested `wiki/` notes in list, search, open, query, check, lint, and link.
- `init` refuses this package checkout unless `--allow-framework-root` is set.
- Graphify output path is `derived/graphify/` when that optional tool is run. It is not a CLI dependency.

## Phase 2: GBrain-Inspired Intelligence Layer (Future)

- Add optional intelligence services that sit on top of the Phase 1 markdown corpus.
- Keep markdown files in `wiki/` as canonical long-term source of truth.
- Evaluate advanced retrieval and reasoning features as optional modules, not core storage.
- When scoping Phase 2, evaluate external tooling candidates such as [Graphify](https://github.com/safishamsi/graphify) and [Hyper-Extract](https://github.com/yifanfeng97/Hyper-Extract) (see [FUTURE_PHASE_2.md](FUTURE_PHASE_2.md)). Graphify is already an optional navigation tool writing `derived/graphify/`. It is not required to install or run llm-wiki.

See [FUTURE_PHASE_2.md](FUTURE_PHASE_2.md) for scope boundaries and future directions.
