# Release Notes: v0.1.0

## Scope

Phase 1 CLI baseline.

## Included Commands

- `init`
- `ingest`
- `list`
- `search`
- `open`
- `summarize`
- `link`
- `check`

## Validation

- Test suite: passing (`pytest -q`).
- CLI smoke flow: passing (`init`, `list`, `check`).

## Highlights

- Local-first CLI workflow implemented with markdown/filesystem source of truth.
- Note schema and consistency checks implemented.
- Ingest manifests and wiki logging implemented.
- Command behavior hardened with stable exit code patterns.
- Regression tests added for command contracts and failure paths.

## Out of Scope Reminder

Phase 1 does not include database storage, vector search, pgvector, knowledge graph runtime, or persistent agent-memory runtime.
