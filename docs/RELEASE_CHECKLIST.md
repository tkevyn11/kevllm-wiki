# Release Checklist (v0.1.0)

## Goal

Ship a stable `v0.1.0` baseline for Phase 1 with reproducible checks, clear versioning, and traceable release notes.

## Pre-Release Checks

- Ensure workspace is clean of temporary ingest artifacts.
- Confirm docs status is current:
  - `docs/ROADMAP.md`
  - `docs/MVP_SCOPE.md`
  - `docs/PRD.md`
- Run test suite:
  - `pytest -q`
- Run basic CLI smoke flow:
  - `llm-wiki init -C .`
  - `llm-wiki list -C .`
  - `llm-wiki check -C .`

## Version Bump Guidance

For `v0.1.0`, keep version values consistent in:

- `pyproject.toml` -> `[project].version`
- `src/llm_wiki/__init__.py` -> `__version__`

Update both from current value to:

- `0.1.0` for first stable Phase 1 baseline (already set)

Future bump rules:

- Patch (`0.1.x`): bug fixes, tests, docs, no CLI contract changes.
- Minor (`0.x.0`): additive command flags/features without breaking existing behavior.
- Major (`x.0.0`): breaking CLI or schema contract changes.

## Release Notes Template

Use this structure for release notes/tag annotation:

- Scope: Phase 1 CLI baseline
- Included commands: `init`, `ingest`, `list`, `search`, `open`, `summarize`, `link`, `check`
- Validation: tests passing and smoke checks passing
- Out of scope reminder: no DB/vector/graph/agent-memory runtime in Phase 1

## Tagging and Publish Steps

If using git tags:

1. Confirm tests and smoke checks pass.
2. Commit all intended changes.
3. Create annotated tag:
   - `git tag -a v0.1.0 -m "Phase 1 CLI baseline"`
4. Push commit and tag:
   - `git push`
   - `git push origin v0.1.0`

If not publishing yet, keep this as an internal readiness checklist.
