# Architecture and Product Decisions

This file records high-impact decisions for Phase 1 with context and trade-offs.

## D-001: Markdown in `wiki/` Is Canonical

- **Context**: The project prioritizes inspectability and long-term portability.
- **Decision**: Structured markdown notes in `wiki/` are the source of truth.
- **Consequences**:
  - Easy manual editing and version control.
  - Future layers must treat markdown corpus as canonical.

## D-002: Filesystem-First, No Database in Phase 1

- **Context**: MVP targets solo usage and low operational complexity.
- **Decision**: Do not introduce database storage in Phase 1.
- **Consequences**:
  - Simpler setup and debugging.
  - Some query operations may be less optimized at larger scale.

## D-003: CLI Is the Primary Interface

- **Context**: Project is explicitly CLI-first and local-first.
- **Decision**: `llm-wiki` commands define all core workflows.
- **Consequences**:
  - Strong automation ergonomics.
  - UI can be deferred without blocking core value.

## D-004: Typer for Command Surface

- **Context**: Need lightweight, maintainable CLI framework in Python.
- **Decision**: Use Typer for command definitions and help output.
- **Consequences**:
  - Fast iteration with type hints.
  - Minimal framework overhead for MVP.

## D-005: Keyword Search First

- **Context**: Need practical search without infrastructure.
- **Decision**: Implement local keyword ranking over markdown in Phase 1.
- **Consequences**:
  - No dependency on embeddings/vector infra.
  - Advanced semantic retrieval deferred to future phase.

## D-006: Frontmatter Schema v1

- **Context**: Notes need consistent metadata and provenance.
- **Decision**: Enforce required fields (`id`, `title`, `type`, `created`, `updated`, `sources`) with optional extensible fields.
- **Consequences**:
  - Better reliability for listing/search/check operations.
  - Slightly more discipline required on note creation.

## D-007: `work/` for Temporary and Operational State

- **Context**: Ingest and validation need machine-managed artifacts.
- **Decision**: Store manifests and transient artifacts under `work/`.
- **Consequences**:
  - Keeps wiki clean and focused on durable knowledge.
  - Operational state remains inspectable and disposable.

## D-008: Starter `wiki/index.md` and `wiki/log.md`

- **Context**: Need consistent navigation and chronology from first use.
- **Decision**: `init` generates `index.md` and `log.md` if missing.
- **Consequences**:
  - Improves discoverability and history tracking.
  - Adds small maintenance responsibilities to ingest/link workflows.

## D-009: Summarization Is Local by Default, LLM Optional

- **Context**: Local-first is a core project goal.
- **Decision**: Default summarize behavior is deterministic local heuristics; optional LLM integration is opt-in.
- **Consequences**:
  - Works offline for baseline workflows.
  - Optional quality improvements available without coupling MVP to cloud.

## D-010: Phase 2 as Additive Intelligence Layer

- **Context**: Project intends later evolution toward GBrain-inspired capabilities.
- **Decision**: Keep Phase 1 modules stable so future indexing/intelligence layers can sit on top without replacing markdown storage.
- **Consequences**:
  - Cleaner migration path.
  - Requires discipline against premature optimization in Phase 1.

## D-011: Optional Viewer and Authoring Integrations Allowed

- **Context**: Tools like web clippers, Obsidian graph view, Marp, and Dataview can improve usability for markdown workflows.
- **Decision**: Allow these as optional, non-core integrations that operate on local files without changing core architecture.
- **Consequences**:
  - Better day-to-day ergonomics for capture, browsing, and presentation.
  - Core CLI remains independent from any specific UI or plugin ecosystem.

## D-012: Phase 2 evaluation candidates (Graphify, Hyper-Extract)

- **Context**: Richer extraction and graph-style tooling may be useful after Phase 1 is stable.
- **Decision**: Treat [Graphify](https://github.com/safishamsi/graphify) and [Hyper-Extract](https://github.com/yifanfeng97/Hyper-Extract) as **Phase 2 evaluation candidates only**; document them in [FUTURE_PHASE_2.md](FUTURE_PHASE_2.md) and do not integrate them into Phase 1 core.
- **Consequences**:
  - Clear boundary: Phase 1 stays filesystem + CLI + keyword search.
  - Future work has named options without committing to either tool or architecture.
