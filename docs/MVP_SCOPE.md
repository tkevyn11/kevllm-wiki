# MVP Scope (Phase 1)

## Objective

Deliver a small, reliable CLI knowledge library for a solo builder. The MVP must be useful in daily note workflows while staying simple to understand and maintain.

## Current MVP Status

- Phase 1 command surface is implemented: `init`, `ingest`, `list`, `search`, `open`, `summarize`, `link`, `check`.
- Core automated tests are in place and passing for happy-path and failure-path validation checks.
- Hardening objectives are completed (error handling and stable exit codes standardized).

## In Scope

- Local library initialization:
  - `llm-wiki init`
- Ingest local source materials into a structured workflow:
  - `llm-wiki ingest`
- Structured markdown notes with YAML frontmatter in `wiki/`.
- Local note listing and filtering:
  - `llm-wiki list`
- Local keyword search over notes:
  - `llm-wiki search`
- Note opening by id/path:
  - `llm-wiki open`
- Local-first summarization utility:
  - `llm-wiki summarize`
- Explicit note relationship support:
  - `llm-wiki link`
- Consistency validation:
  - `llm-wiki check`

## Out of Scope (Phase 1)

- Full visual knowledge management UI.
- Real-time sync or multi-device sync service.
- Multi-user collaboration and permissions.
- Team workflow orchestration.
- Cloud-native architecture requirements.
- Obsidian feature parity.

## Explicitly Deferred

- Databases as core storage.
- Vector search and pgvector integration.
- Knowledge graph extraction and graph query engines.
- Persistent agent-memory systems.

## Acceptance Criteria

- All commands in CLI spec are implemented with stable behavior.
- Files in `wiki/` remain manually editable and readable.
- `llm-wiki check` catches invalid schema and broken links.
- Default operation works entirely on local filesystem without mandatory external services.

## Acceptance Progress

- `All commands in CLI spec are implemented`: Completed.
- `Files in wiki remain manually editable and readable`: Completed.
- `llm-wiki check catches invalid schema and broken links`: Completed (with strict-mode checks available).
- `Default operation works entirely on local filesystem`: Completed.
