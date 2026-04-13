# Tech Stack (Phase 1)

## Runtime and Language

- **Language**: Python 3.11+
- **Reason**: strong CLI ecosystem, readable code, fast iteration for solo development.

## CLI Framework

- **Choice**: Typer
- **Reason**: lightweight, type-hint friendly, clear command/option definitions, and good help output with minimal boilerplate.

## Core Libraries

- **Filesystem**: `pathlib` (standard library)
- **Metadata parsing**: `PyYAML` for frontmatter blocks
- **Text processing**: standard library (`re`, `datetime`, `json`, `textwrap`)
- **Command execution/open behavior**: `os`, `subprocess`, `webbrowser`, platform-specific helpers

## Search Approach

- **Phase 1 default**: local in-process keyword search over markdown files.
- **Ranking**: simple relevance score (title/frontmatter/body weighting).
- **Scope**: no embeddings, no vector index, no external search service.

## Testing and Quality

- **Test framework**: pytest
- **Suggested dev tooling**:
  - ruff for linting
  - mypy (optional) for static type checks

## Packaging and Layout

- **Recommended package layout**: `src/llm_wiki/`
- **Reason**: avoids import path ambiguity and scales cleanly as modules grow.

## Storage Model

- Local filesystem only in Phase 1:
  - `raw/` for original sources
  - `wiki/` for structured markdown notes
  - `work/` for temporary artifacts and ingest manifests

## External Dependencies Policy

- Keep dependency surface small.
- Prefer standard library unless a third-party package adds clear value.
- Avoid introducing infrastructure dependencies during MVP.

## Not Included in Phase 1

- Database engines (SQLite/Postgres as primary source of truth).
- pgvector or any embedding-first architecture.
- Graph databases or graph traversal infrastructure.
- Heavy frontend frameworks.

## Optional Tooling (Non-Core)

- **Web clipper tools** (external): produce markdown inputs for `raw/`.
- **Obsidian** (optional viewer): useful for browsing/backlinks/graph visualization over `wiki/`.
- **Marp** (optional export): generate slide decks from markdown notes.
- **Dataview** (optional query plugin): run local queries against note frontmatter.

These tools are optional and must not become required runtime dependencies for CLI functionality.
