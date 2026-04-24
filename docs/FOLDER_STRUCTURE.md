# Folder Structure

## Library Root

In this project, repository root and library root are the same by default.

```text
d:\my LLM-wiki/
├─ raw/                     # Original source materials
│  ├─ original/             # Optional: untouched originals (pdf/docx/pptx)
│  └─ processed/            # Optional: extracted text/markdown from preprocessors
├─ wiki/                    # Structured markdown knowledge base
│  ├─ index.md              # Catalog of wiki notes
│  └─ log.md                # Chronological activity log
├─ schema/                  # Schema-layer conventions and workflows
│  ├─ SCHEMA.md             # Canonical ingest/query/lint contract
│  └─ CLAUDE.md             # LLM maintainer instructions (Karpathy-style)
├─ work/                    # Temporary processing artifacts and manifests
├─ docs/                    # Product and architecture documentation
├─ src/
│  └─ llm_wiki/             # Python package (planned implementation layout)
├─ tests/                   # Automated tests
└─ README.md                # Project overview
```

## Directory Responsibilities

- `raw/`
  - Stores untouched source inputs used for note generation.
  - Optional split for better control:
    - `raw/original/` for original binary docs.
    - `raw/processed/` for extracted markdown/text used for better search quality.
- `wiki/`
  - Stores canonical markdown notes and wiki-level index/log files.
- `schema/`
  - Stores conventions that govern ingest, query, lint, and note schema rules.
  - Includes LLM maintainer instruction files consumed before operations.
- `work/`
  - Stores temporary and operational data (ingest manifests, intermediate artifacts).
- `docs/`
  - Stores decision records, architecture docs, and project specifications.
- `src/llm_wiki/`
  - Planned home for CLI and core modules.
- `tests/`
  - Planned test suite for commands and core logic.

## Structure Principles

- Keep source of truth in markdown files under `wiki/`.
- Keep operational state explicit and disposable under `work/`.
- Avoid hidden state in Phase 1.
