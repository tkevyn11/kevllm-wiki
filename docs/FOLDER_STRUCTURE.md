# Folder Structure

## Library Root

In this project, repository root and library root are the same by default.

```text
d:\my LLM-wiki/
├─ raw/                     # Original source materials
├─ wiki/                    # Structured markdown knowledge base
│  ├─ index.md              # Catalog of wiki notes
│  └─ log.md                # Chronological activity log
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
- `wiki/`
  - Stores canonical markdown notes and wiki-level index/log files.
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
