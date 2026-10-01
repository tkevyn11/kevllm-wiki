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
- **Declared readers**: `pypdf` for PDF text and `python-docx` for DOCX text. PPTX slide text in the extraction service uses the standard-library ZIP/XML reader. `python-pptx` is not a dependency.
- **Text processing**: standard library (`re`, `datetime`, `json`)
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
  - `raw/` for source copies
  - `wiki/` for canonical markdown notes
  - `work/` for transient artifacts and ingest manifests
  - `derived/` for rebuildable extracts (`llm-wiki ingest --extract`) and future indexes

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

## Optional local OCR

Not required for `pip install -e .` or for `llm-wiki ingest`.

- **Extra**: `pip install -e ".[ocr]"` installs `paddleocr` and `pymupdf`.
- **Engine**: PaddlePaddle 3.x is separate. A CPU example is `python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/`.
- **Use**: `llm-wiki ingest <source> --extract --ocr`. `llm-wiki review approve` is a separate local decision and does not call OCR again.
- **Scope**: local images and scanned PDFs. No cloud OCR API. Model setup may download weights; source files stay on the machine.
