# Folder Structure

## Two roots

The framework checkout and a user library should be different directories.

```text
kevllm-wiki/                 # Git checkout of this package
├─ src/llm_wiki/             # CLI package
├─ tests/
├─ docs/
├─ schema/                   # Maintainer contract shipped with the framework
└─ README.md

my-knowledge/                # Created with: llm-wiki init
├─ raw/                      # Source material and provenance copies
├─ wiki/                     # Canonical Markdown + YAML
│  ├─ index.md
│  └─ log.md
├─ work/                     # Transient manifests and logs
├─ derived/                  # Rebuildable outputs (not created by init yet)
├─ docs/                     # Library-local notes, separate from framework docs
└─ schema/                   # Starter schema files for that library
```

Preferred setup:

```bash
pip install -e .
mkdir my-knowledge
cd my-knowledge
llm-wiki init
```

`init` does not create `derived/`. That directory is the contract for later graph, vector, semantic, and extraction output. It is gitignored at the framework repo root so a local experiment there is not committed by accident. `init` will not overwrite starter files that already exist.

`init` refuses to run in this framework checkout (the directory that contains this package's `pyproject.toml` and `src/llm_wiki/`). Use a separate folder. Maintainers can pass `--allow-framework-root` when they intentionally want starter files inside the checkout.

## Runtime layers

- `raw/` holds copies of ingested sources. It may be private. Processing commands do not edit the original file outside the library.
- `wiki/` is canonical. Notes are Markdown with YAML frontmatter.
- `work/` is transient. `ingest-manifest.jsonl` can contain absolute local paths.
- `derived/` is rebuildable and never canonical. Optional tools (Graphify, semantic indexes, MCP caches) must not replace `wiki/`.

Graphify writes rebuildable navigation under `derived/graphify/`. Those files are not a second source of truth. `wiki/` may contain nested note folders; retrieval and validation commands see those notes.

## Framework directories

- `src/llm_wiki/` is the installed package (`cli.py`, `commands.py`, `core.py`).
- `tests/` is the automated suite, including the CLI characterization tests.
- `docs/` in the Git checkout is product documentation. `docs/` inside a user workspace is created empty by `init` and is not this manual.
- `schema/` in the Git checkout is the maintainer contract. `init` writes a short starter `schema/SCHEMA.md` and `schema/CLAUDE.md` only when the library does not already have them.

## Principles

- Keep knowledge in `wiki/`.
- Treat `work/` and `derived/` as disposable.
- Do not commit user `raw/`, `wiki/`, `work/`, or `derived/` from a real library into the framework repository.
