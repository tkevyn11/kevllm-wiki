# Roadmap

## Guiding Principle

Phase 1 is intentionally narrow: deliver a robust local CLI workflow around markdown files. Phase 2 explores intelligence features only after Phase 1 is stable and useful.

## Phase 1: CLI LLM-Wiki Library

## Current Status

- **Current stage**: Phase 1 implemented and hardened.
- **Milestones completed**: Milestone 1 through Milestone 6.
- **Next stage**: Phase 1 maintenance and optional refactor cleanup before Phase 2 planning.

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
- Implement `llm-wiki summarize` with local default behavior and optional LLM backend.
- Improve output formatting and command help text.

### Milestone 6: Hardening

- Status: Completed
- Add automated tests for schema, ingest, search, and checks.
- Add CLI error handling and stable exit codes.
- Finalize docs for usage and maintenance.

## Phase 2: GBrain-Inspired Intelligence Layer (Future)

- Add optional intelligence services that sit on top of the Phase 1 markdown corpus.
- Keep markdown files in `wiki/` as canonical long-term source of truth.
- Evaluate advanced retrieval and reasoning features as optional modules, not core storage.

See [FUTURE_PHASE_2.md](FUTURE_PHASE_2.md) for scope boundaries and future directions.
