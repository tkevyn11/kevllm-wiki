# Release Notes: v0.2.0

Release candidate. This note describes the `feat/generic-framework-v0.2` tree. It is not a Git tag and it is not a PyPI release.

## Version

`0.2.0` in `pyproject.toml` and `src/llm_wiki/__init__.py`.

## What changed

- The public tree is a generic local framework. User libraries stay outside the checkout. `raw/`, `wiki/`, `work/`, and `derived/` at the repo root are gitignored.
- `llm-wiki ingest` without flags is unchanged: every file becomes a note.
- `llm-wiki ingest <source> --extract` runs a local quality gate. Only `clean` text becomes a wiki note. The new events in `derived/extraction/manifests/` use workspace-relative paths and can be rebuilt. They do not store absolute machine paths.
- Text, Markdown, PDF text layers, DOCX, and PPTX slide text are extracted locally. PPTX uses the standard-library ZIP reader.
- `llm-wiki ingest <source> --extract --ocr` adds optional local OCR for images and scanned PDFs. Install it with `pip install "llm-wiki[ocr]"` (or `pip install -e ".[ocr]"` from a checkout). PaddlePaddle 3.x is a separate engine and is not part of that extra. OCR text goes through the same quality gate. Model setup may download weights; source files are not uploaded.
- `llm-wiki review list`, `show`, `approve`, and `reject` are the only way a `review` extract becomes a note, or is refused. Decisions are appended under `derived/extraction/manifests/review.jsonl`.
- `list`, `search`, `open`, `query`, `check`, `lint`, and `link` see notes in nested `wiki/` folders. `wiki/index.md` and `wiki/log.md` are not notes. Duplicate ids are reported across folders.
- `init` exits 2 inside this package checkout. Use a separate directory, or `--allow-framework-root` for a maintainer override.
- Graphify, when you run it, should write `derived/graphify/`. It is not a required dependency and it is not run by the CLI.

## Not in this version

- OCR for image-only DOCX or PPTX. Those files stay `ocr_needed`.
- MCP servers, vector or semantic search, and GBrain or Semantica integration.
- A web or terminal UI for review.
- Cloud storage or a hosted knowledge service.
- A chosen license. The repository does not include one yet.

## Install check

Base install does not pull OCR:

```bash
pip install llm-wiki
```

From a checkout, tests use `pip install -e ".[dev]"`.
