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
   - For PDF-heavy workflows, keep originals under `raw/original/`.
   - Optionally preprocess PDFs into markdown/text and save outputs under `raw/processed/`.
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
   - Default ingest writes a `## Summary` section (`--summarize`).
   - You can disable this with `--no-summarize`.
5. **Index and log updates**
   - `wiki/index.md` is updated with note reference.
   - `wiki/log.md` appends ingest event summary.
6. **Optional relationship pass**
   - With `--link-suggestions`, ingest proposes and writes related-note links.
   - With `--touch-related`, ingest also refreshes summaries for newly linked notes.
7. **Validation**
   - Run schema and link checks (implicitly or via explicit `llm-wiki check`).

## Ingest Modes and When to Use Them

- `llm-wiki ingest <input>`
  - Use for normal day-to-day ingest.
- `llm-wiki ingest <input> --link-suggestions`
  - Use when new sources are likely related to existing notes.
- `llm-wiki ingest <input> --link-suggestions --touch-related`
  - Use when you want immediate refresh of linked notes after ingest.
- `llm-wiki ingest <input> --no-summarize`
  - Use when source extraction quality is low and you prefer manual summary editing.

## Recommended PDF Preprocessing Pattern (Optional)

For better search quality on PDF/doc-based workflows:

1. Keep original files in `raw/original/`.
2. Use an external parser (for example, `opendataloader-pdf`) to extract text/markdown.
3. Save extracted outputs in `raw/processed/`.
4. Ingest the processed text/markdown with `llm-wiki ingest`.
5. Keep source attribution pointing to both original and processed artifacts when possible.

This keeps Phase 1 architecture unchanged while improving retrieval quality.

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
