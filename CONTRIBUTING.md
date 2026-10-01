# Contributing

This repository is the llm-wiki framework. Keep personal notes out of it.

## Setup

```bash
python -m venv .venv
```

Activate the virtualenv, then from the repository root:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

Optional OCR is `pip install -e ".[ocr]"` plus a separate PaddlePaddle install. The normal test suite does not download OCR models.

## Workspace

Run `llm-wiki init` in a directory that is not this checkout. `init` exits 2 if you point it at the package source tree. Use `--allow-framework-root` only when you mean to do that.

Do not commit `raw/`, `wiki/`, `work/`, `derived/`, `.env` files, credentials, or a real library. Synthetic examples are fine.

## Pull requests

Describe the behavior change and how you tested it. Do not add a required network service, a new database, or a dependency the base install does not need. Keep `wiki/` markdown as the canonical store.
