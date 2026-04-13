# Ingest Workflow (Phase 1)

## Purpose

Define a predictable, local ingest process that transforms raw materials into structured wiki notes while preserving source attribution and keeping all artifacts inspectable.

## Inputs

- Local files (single item)
- Local directories (batch)
- Optional URL references (recorded as metadata; retrieval behavior can be added later)
- Web-clipped markdown files (treated as standard local files)
- Local image assets (for example under `raw/assets/`)

## Workflow Steps

1. **Acquire source**
   - User provides file path, directory path, or URL metadata.
2. **Register ingest**
   - CLI appends entry to `work/ingest-manifest.jsonl`.
   - Manifest captures timestamp, input reference, and status.
3. **Material placement**
   - For files/directories, source is copied into `raw/` or indexed by stable reference according to ingest policy.
   - Original source remains unchanged.
   - For image-heavy clipped content, keep downloaded images local and preserve relative links where possible.
4. **Note creation/update**
   - Create new note or update existing note in `wiki/`.
   - Ensure required frontmatter fields and source attribution are present.
5. **Index and log updates**
   - `wiki/index.md` is updated with note reference.
   - `wiki/log.md` appends ingest event summary.
6. **Validation**
   - Run schema and link checks (implicitly or via explicit `llm-wiki check`).

## Idempotence Policy

- Re-ingesting the same source should not produce duplicate note ids.
- Re-ingest behavior:
  - existing note may be updated
  - manifest gets a new event record
  - source attribution list can append a new `ingested_at` entry when appropriate

## Human-in-the-Loop Expectations

- User can review generated note content after each ingest.
- Manual edits are first-class and preserved.
- Ingest should prefer incremental updates over full rewrites.

## Manifest Example

```json
{
  "event": "ingest",
  "ingested_at": "2026-04-13T20:20:00Z",
  "input": "raw/papers/attention-is-all-you-need.pdf",
  "status": "success",
  "note_id": "transformer-attention"
}
```
