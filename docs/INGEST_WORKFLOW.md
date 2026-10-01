# Ingest Workflow (Phase 1)

## Purpose

Define a predictable, local ingest process that transforms raw materials into structured wiki notes while preserving source attribution and keeping all artifacts inspectable.

## Inputs

- Local files (single item)
- Local directories (recursive batch)
- Web-clipped markdown files saved on disk (treated as ordinary local files)
- The CLI does not fetch URLs

## Workflow Steps

1. **Acquire source**
   - User provides a local file or directory path.
   - Text-like files are read directly. PDF text uses `pypdf` when that import works. DOCX text uses `python-docx` when that import works.
2. **Register ingest**
   - CLI appends one JSON object per file to `work/ingest-manifest.jsonl`.
   - `input` is the absolute local path. Treat the manifest as private.
3. **Material placement**
   - The source is copied into `raw/` by basename.
   - A directory walk is recursive, but nested relative folders are not preserved.
   - The file outside the library is not modified.
   - If `raw/<basename>` already exists, the copy uses a `-2`, `-3`, ... suffix.
4. **Note creation**
   - Create a new note in `wiki/`. An existing note with the same id is not rewritten; the new id is suffixed the same way.
   - Required frontmatter and source attribution are written on the new note.
   - Default ingest writes a `## Summary` section (`--summarize`).
   - `--no-summarize` skips that section.
5. **Index and log updates**
   - `wiki/index.md` is updated with note reference.
   - `wiki/log.md` appends ingest event summary.
6. **Optional relationship pass**
   - With `--link-suggestions`, ingest proposes and writes related-note links.
   - With `--touch-related`, ingest also refreshes summaries for newly linked notes.
7. **Validation**
   - Ingest does not run `check` itself. Run `llm-wiki check` or `llm-wiki lint` afterward.

## Ingest Modes and When to Use Them

- `llm-wiki ingest <input>`
  - Use for normal day-to-day ingest.
- `llm-wiki ingest <input> --link-suggestions`
  - Use when new sources are likely related to existing notes.
- `llm-wiki ingest <input> --link-suggestions --touch-related`
  - Use when you want immediate refresh of linked notes after ingest.
- `llm-wiki ingest <input> --no-summarize`
  - Use when source extraction quality is low and you prefer manual summary editing.

## PDF and Office Files

Ingest without `--extract` can read text from a `.pdf` via `pypdf` and from a `.docx` via `python-docx` when those imports succeed. That path has no quality gate and no OCR. If that text is poor, ingest a markdown or text export instead, or use `--no-summarize` and edit the note.

## Re-ingest Behavior

Re-ingest does not update the existing note.

- The first ingest of `sample-paper.md` creates `raw/sample-paper.md` and `wiki/sample-paper.md`.
- A second ingest of the same filename creates `raw/sample-paper-2.md` and `wiki/sample-paper-2.md`.
- The first note, including any manual edits, stays as it was.
- The manifest gets a new event for the new note id.

## Human-in-the-Loop Expectations

- Review the new note after ingest.
- Edit `wiki/` directly. Later ingests of the same filename will not overwrite that file.
- Without `--extract`, ingest still creates a note for every file and does not run the quality gate. Weak extracts should be fixed in the note or ingested with `--no-summarize`.
- `llm-wiki ingest <input> --extract` runs the local quality gate. Only `clean` results become wiki notes. `review` stays under `derived/extraction/text/` and is not promoted automatically.
- `llm-wiki ingest <input> --extract --ocr` adds optional local OCR for images and scanned PDFs. The OCR text still has to pass the quality gate. See [EXTRACTION.md](EXTRACTION.md).

## Manifest Example

```json
{
  "event": "ingest",
  "ingested_at": "2026-04-13T20:20:00Z",
  "input": "/path/to/sample-paper.md",
  "status": "success",
  "note_id": "sample-paper"
}
```
