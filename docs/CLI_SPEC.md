# CLI Specification (Phase 1)

## CLI Name

- Command: `llm-wiki`
- Scope: local library operations over filesystem markdown notes.

## Global Options

- `--library PATH`, `-C PATH`
  - Library root directory.
  - Default: current working directory.
- `--json`
  - Machine-readable output for commands that return collections (`list`, `search`).

## Exit Codes

- `0`: success
- `1`: runtime failure or invalid state
- `2`: invalid command arguments
- `3`: validation failure (used by `check`)
- `4`: target not found (note id/path not resolved)

## Command: `init`

Initialize a library structure.

### Usage

`llm-wiki init [--library PATH]`

### Behavior

- Creates missing folders: `raw/`, `wiki/`, `work/`, `docs/`.
- Creates starter files if absent:
  - `wiki/index.md`
  - `wiki/log.md`
- Does not overwrite existing user content.

## Command: `ingest`

Ingest source materials and produce/update structured notes.

### Usage

`llm-wiki ingest <input> [--library PATH] [--type TYPE] [--title TITLE] [--id NOTE_ID] [--summarize/--no-summarize] [--link-suggestions] [--touch-related]`

### Arguments

- `<input>`: local file path or directory path.

### Behavior

- Registers ingest operation in `work/ingest-manifest.jsonl`.
- Copies or references sources under `raw/` according to ingest policy.
- Creates or updates markdown notes in `wiki/`.
- Adds source attribution metadata in note frontmatter.
- `--summarize` (default) writes a `## Summary` section during ingest.
- `--no-summarize` skips automatic summary generation.
- `--link-suggestions` adds related-note links based on keyword overlap.
- `--touch-related` refreshes summaries/index entries for related notes linked in the same ingest pass.

## Command: `list`

List notes in the wiki.

### Usage

`llm-wiki list [--library PATH] [--type TYPE] [--tag TAG] [--json]`

### Behavior

- Returns notes with core metadata:
  - `id`, `title`, `type`, `updated`, `path`
- Supports text or JSON output.

## Command: `search`

Keyword search across note metadata and content.

### Usage

`llm-wiki search <query> [--library PATH] [--limit N] [--json]`

### Behavior

- Searches title, frontmatter fields, and markdown body.
- Returns ranked results with snippets and paths.
- Uses local keyword scoring only in Phase 1.

## Command: `open`

Open a note in the default system handler.

### Usage

`llm-wiki open <id-or-path> [--library PATH]`

### Behavior

- Resolves note by id first, then by direct path.
- Opens via platform handler:
  - Windows: `os.startfile`
  - macOS: `open`
  - Linux: `xdg-open`
- Returns exit code `4` if target cannot be resolved.

## Command: `summarize`

Summarize a note or source.

### Usage

`llm-wiki summarize <id-or-path> [--library PATH] [--mode local|llm] [--write]`

### Behavior

- `local` mode (default): deterministic heuristic summary.
- `llm` mode: optional adapter if configured.
- Does not require cloud services for default mode.
- `--write`: writes/updates a `## Summary` section in the note and refreshes index/log metadata.

## Command: `link`

Create note-to-note relationships.

### Usage

`llm-wiki link <from-id> <to-id> [--library PATH] [--relation REL] [--bidirectional]`

### Behavior

- Updates `related` metadata in frontmatter.
- Default is bidirectional link update.
- Does not rewrite body content unless explicitly enabled in future versions.

## Command: `check`

Validate library consistency.

### Usage

`llm-wiki check [--library PATH] [--strict]`

### Behavior

- Validates required frontmatter fields.
- Checks duplicate ids.
- Checks broken internal links.
- Checks source attribution shape.
- Returns exit code `3` on validation failures.

## Command: `query`

Ask a question against the wiki and synthesize a citation-backed answer.

### Usage

`llm-wiki query "<question>" [--library PATH] [--top-k N] [--save]`

### Behavior

- Retrieves top matching notes from local wiki content.
- Produces a synthesized answer with source citations.
- `--save` writes the answer back into `wiki/` as a `query-*` note.

## Command: `lint`

Run a health-check pass inspired by Karpathy-style wiki maintenance.

### Usage

`llm-wiki lint [--library PATH] [--strict]`

### Behavior

- Runs structural checks (same baseline as `check`).
- Adds health warnings (for example orphan notes and notes missing summary sections).
- Intended for periodic maintenance passes, not just schema validation.
