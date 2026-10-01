# CLI Specification (Phase 1)

This file describes the behavior locked by the characterization tests on `feat/generic-framework-v0.2`. It is not a wishlist.

## CLI Name

- Command: `llm-wiki`
- Scope: local library operations over filesystem markdown notes.

## Global Options

- `--library PATH`, `-C PATH`
  - Library root directory.
  - Default: current working directory.
- `--json`
  - Machine-readable output for `list` and `search`.

## Exit Codes

- `0`: success, including empty `list` and `search` results
- `1`: reserved for unexpected runtime failure (not returned by the commands below)
- `2`: invalid arguments, missing ingest input, unsupported summarize mode, a query with no usable terms, `--ocr` without `--extract`, or `--ocr` when the optional local OCR packages are not installed
- `3`: validation failure from `check` or `lint`, or a `--extract` batch that contains `reject` or `error`
- `4`: target not found (note id or path not resolved)

## Command: `init`

Initialize a library structure.

### Usage

`llm-wiki init [--library PATH]`

### Behavior

- Creates missing folders: `raw/`, `wiki/`, `work/`, `docs/`, `schema/`.
- Creates these files only when absent:
  - `wiki/index.md`
  - `wiki/log.md`
  - `schema/SCHEMA.md`
  - `schema/CLAUDE.md`
- Running `init` again does not overwrite existing starter content.
- Does not create `derived/`.

## Command: `ingest`

Copy local sources into the library and create notes.

### Usage

`llm-wiki ingest <input> [--library PATH] [--type TYPE] [--title TITLE] [--id NOTE_ID] [--summarize/--no-summarize] [--link-suggestions] [--touch-related] [--extract]`

### Arguments

- `<input>`: local file or directory. URLs are not fetched.

### Behavior

- Walks a directory recursively. Each file is copied into `raw/` by basename, not by relative path.
- Does not modify the original file outside the library.
- If the raw basename already exists, the copy is named `<stem>-2`, then `<stem>-3`, and so on.
- Creates a new note `wiki/<id>.md`. The id defaults to a slug of the filename. If that note already exists, the id is suffixed the same way (`project-alpha-2`). The previous note is left unchanged.
- Writes required frontmatter, a `## Source` section, and by default a `## Summary`.
- `--no-summarize` omits the summary section.
- `--summarize` is the default and uses the local heuristic (up to three sentences of extracted text).
- Appends one JSON object per file to `work/ingest-manifest.jsonl`. The `input` field is the absolute local path of that file.
- Updates `wiki/index.md` and appends `wiki/log.md`.
- `--link-suggestions` adds `related` ids when keyword overlap is strong enough.
- `--touch-related` refreshes summaries and index lines for notes linked in that same pass.
- Text-like files (`.md`, `.txt`, and similar) are read as text. `.pdf` uses `pypdf` when import succeeds. `.docx` uses `python-docx` when import succeeds.
- Without `--extract`, every file becomes a wiki note. `work/ingest-manifest.jsonl` keeps the legacy event `ingest`, including an absolute `input` path.
- `--extract` is the quality-gated path. It does not change the command above when the flag is absent. See [EXTRACTION.md](EXTRACTION.md).

### `--extract`

- Copies each file into `raw/` using its path relative to the input file or directory, so two files with the same basename stay distinct.
- Runs local detection, extraction, and the quality gate. OCR is not called unless `--ocr` is also set.
- Writes rebuildable output under `derived/extraction/`.
- Creates a canonical wiki note only for `clean`. The note body contains the extracted text, not a fenced copy of the source bytes. Optional frontmatter: `source_file` (workspace-relative), `source_sha256`, `extraction_status`.
- `review`, `ocr_needed`, `skip`, `reject`, and `error` do not create a wiki note.
- A directory is processed file by file. One bad file does not stop the others.
- Exit `0` when every file is `clean`, `review`, `ocr_needed`, or `skip`.
- Exit `3` when any file is `reject` or `error`, after the rest of the batch has still been processed.
- Records portable events in `derived/extraction/manifests/ingest.jsonl` (`event: extract`, `schema_version: 1`). That file is separate from the legacy `work/ingest-manifest.jsonl` and does not store absolute paths.
- `--link-suggestions` and `--touch-related` still apply to notes that were actually created.

### `--extract --ocr`

- `--ocr` without `--extract` exits `2`. It does not ingest the file.
- Images, and PDFs with no meaningful text layer, go to the local PaddleOCR provider. The recognized text is normalized and run through the same quality gate. OCR success is not automatically `clean`.
- A wiki note is created only when the post-OCR status is `clean`. `review` stays under `derived/extraction/text/` and is not promoted.
- Scanned PDFs are rendered on this machine with PyMuPDF, one page at a time, and the text keeps `## Page N` headings.
- DOCX and PPTX files that have no text layer stay `ocr_needed`.
- A missing OCR install exits `2` with the install command. The command does not skip OCR and continue.
- Portable events gain `ocr_used`, `ocr_provider`, and `ocr_pages`. Those fields do not store absolute paths or model-cache directories.
- Base install remains `pip install -e .`. The OCR extra is `pip install -e ".[ocr]"`. PaddlePaddle is a separate local engine; see [EXTRACTION.md](EXTRACTION.md).

## Command: `list`

List notes in the wiki.

### Usage

`llm-wiki list [--library PATH] [--type TYPE] [--tag TAG] [--json]`

### Behavior

- Reads top-level `wiki/*.md`, excluding `index.md` and `log.md`.
- Does not descend into subfolders.
- Prints `id`, `type`, `updated`, and `title`. `--json` emits those fields plus `path`.
- `--type` keeps notes whose `type` is an exact match.
- `--tag` keeps notes whose `tags` list contains that tag.
- Prints `No notes found.` and exits `0` when nothing matches.

## Command: `search`

Keyword search across note metadata and content.

### Usage

`llm-wiki search <query> [--library PATH] [--limit N] [--json]`

### Behavior

- Uses the same top-level note set as `list`.
- Matches a case-insensitive substring of title, dumped frontmatter, and body.
- Score is `5` when the substring is in the title, plus the number of occurrences in the combined text. Higher scores are listed first.
- Prints `No matches.` and exits `0` when nothing matches.
- Local keyword scoring only. No embeddings.

## Command: `open`

Open a note in the default system handler.

### Usage

`llm-wiki open <id-or-path> [--library PATH]`

### Behavior

Resolution order:

1. If the argument is an existing filesystem path, that path is opened.
2. Otherwise `wiki/<argument>.md` (suffix added when missing).
3. Otherwise the note whose frontmatter `id` equals the argument.

An existing file in the current directory wins over a note id of the same name.

Opens via the platform handler: Windows `os.startfile`, macOS `open`, Linux `xdg-open`. Exit code `4` if nothing resolves.

## Command: `summarize`

Summarize a note locally.

### Usage

`llm-wiki summarize <id-or-path> [--library PATH] [--mode local] [--write]`

### Behavior

- Default `--mode local` builds a short heuristic summary from the note body, or from linked source files when the body has no usable prose.
- Any other `--mode` exits `2` with `Only local mode is currently implemented.`
- `--write` replaces or inserts `## Summary`, leaves other sections in place, and refreshes the index and log.
- Without `--write`, the note is not modified.

## Command: `link`

Create a frontmatter relationship between two notes.

### Usage

`llm-wiki link <from-id> <to-id> [--library PATH] [--relation REL] [--bidirectional/--no-bidirectional]`

### Behavior

- Default `--relation related`. The ids are stored on that frontmatter key, not as a markdown link in the body.
- Default `--bidirectional` updates both notes. `--no-bidirectional` updates only the from-note.
- Linking the same pair again does not duplicate the id.
- A missing note exits `4`.
- `check` validates the `related` key. Other relation names are stored and are not part of that check.

## Command: `check`

Validate library consistency.

### Usage

`llm-wiki check [--library PATH] [--strict]`

### Behavior

- Required frontmatter: `id`, `title`, `type`, `created`, `updated`, `sources`.
- Duplicate ids fail.
- A `related` id that does not match a note fails.
- A relative or root markdown link fails when neither the note-relative path nor the library-root path exists.
- `http://`, `https://`, and `mailto:` links are ignored by that check.
- `--strict` also requires `sources` to be a list.
- Exit code `3` when any of the above fails.

## Command: `query`

Answer a question from notes already in the wiki.

### Usage

`llm-wiki query "<question>" [--library PATH] [--top-k N] [--save]`

### Behavior

- Splits the question into case-insensitive terms longer than two characters. If none remain, exits `2`.
- Scores notes by term counts in title, frontmatter, and body. Notes whose `type` is `query` are skipped.
- Prints an answer made from those notes' summary sections, then citations. This is local text selection, not a model call.
- With no matches, prints `No relevant notes found.` and exits `0`.
- `--save` writes `wiki/query-<slug>.md` with type `query`. Without `--save`, no note is written.

## Command: `lint`

Run structural checks and health warnings.

### Usage

`llm-wiki lint [--library PATH] [--strict]`

### Behavior

- Uses the same structural rules as `check`, including `--strict`.
- Structural failures exit `3` and do not print warnings.
- When structure is valid, warnings exit `0`. Current warnings: a note with no inbound `related` link, and a note whose body has no `## Summary` section.
