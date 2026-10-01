# Release Checklist (v0.2.0)

## Goal

Prepare a `0.2.0` release candidate that can be installed from a wheel, tested without OCR models, and reviewed before any tag or PyPI publish.

The candidate commit does not create the `v0.2.0` tag.

## Pre-Release Checks

- Confirm `pyproject.toml` and `src/llm_wiki/__init__.py` both say `0.2.0`.
- Confirm the branch is `feat/generic-framework-v0.2` and `main` is untouched.
- Run `pytest -q` from a checkout (`pip install -e ".[dev]"`). The suite must not download OCR models.
- Build with `python -m build`. Do not commit `dist/`.
- Install the wheel in a fresh virtualenv outside this repository and run `llm-wiki --help`.
- In a temporary directory outside this checkout, run:
  - `llm-wiki init`
  - `llm-wiki ingest sample.md --extract`
  - `llm-wiki list`
  - `llm-wiki search "sample"`
  - `llm-wiki check`
  - `llm-wiki lint`
  - `llm-wiki review list`
- Do not initialize this framework checkout as a knowledge base.
- Read [RELEASE_NOTES_v0.2.0.md](RELEASE_NOTES_v0.2.0.md) and [PRIVACY.md](PRIVACY.md).

## Version locations

- `pyproject.toml` -> `[project].version`
- `src/llm_wiki/__init__.py` -> `__version__`

Bump rules after this candidate:

- Patch (`0.2.x`): bug fixes, tests, docs, no CLI contract changes.
- Minor (`0.x.0`): additive commands or flags without breaking existing behavior.
- Major (`x.0.0`): breaking CLI or schema contract changes.

## Included commands

`init`, `ingest`, `list`, `search`, `open`, `summarize`, `link`, `check`, `query`, `lint`, `review`.

## Not in this version

Image-only DOCX/PPTX OCR, MCP, vector or semantic search, GBrain, Semantica, a review UI, and cloud storage. License: MIT.

## Tag and publish

Do these only after the candidate is accepted. They are not part of the candidate commit.

1. Open the pull request and merge.
2. Create the annotated tag `v0.2.0`.
3. Push the tag.
4. Publish to PyPI only as a separate decision.
