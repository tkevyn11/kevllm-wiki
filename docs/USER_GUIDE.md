# LLM-Wiki User Guide

LLM-Wiki is a local command-line tool. Markdown files with YAML frontmatter in `wiki/` are the source of truth. Search, summary, and query all run on your machine.

## Framework checkout and user workspace

Keep those separate.

```text
framework checkout     this Git repository (source, tests, docs)
user workspace         any other folder you initialize with llm-wiki init
```

```bash
pip install -e .
mkdir my-knowledge
cd my-knowledge
llm-wiki init
```

You can also pass `--library` / `-C` when the shell is not already in the workspace. Prefer that over running `init` inside the framework checkout. Repo-root `raw/`, `wiki/`, `work/`, and `derived/` are gitignored, but mixing a real library into the framework tree is still easy to get wrong. Details are in [PRIVACY.md](PRIVACY.md) and [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md).

## Data layers

```text
raw/       source material and provenance copies
wiki/      canonical Markdown and YAML notes
work/      transient manifests and logs
derived/   rebuildable indexes and extraction output (not canonical)
```

`init` creates `raw/`, `wiki/`, `work/`, `docs/`, and `schema/`, plus starter `wiki/index.md`, `wiki/log.md`, `schema/SCHEMA.md`, and `schema/CLAUDE.md` when those files are missing. A second `init` does not overwrite them.

## Commands

| Command | What it does now |
|---|---|
| `init` | Create the library folders and starter files if missing. |
| `ingest` | Copy a local file or directory into `raw/` and create a new note. |
| `list` | List top-level `wiki/*.md` notes. Optional `--type`, `--tag`, and `--json`. |
| `search` | Case-insensitive keyword search. A title hit ranks above a body-only hit. |
| `open` | Open a note with the platform handler. |
| `summarize` | Local heuristic summary. `--write` updates `## Summary` and keeps the rest of the note. |
| `link` | Add a frontmatter relation. Default key is `related`, both directions. |
| `check` | Validate required fields, duplicate ids, related ids, and broken markdown links. |
| `query` | Print a local answer from matching notes, with citations. `--save` writes a `query-*` note. |
| `lint` | Same structural checks as `check`, plus warnings for orphan notes and missing summaries. |

`index.md` and `log.md` are not listed as notes. Notes in subfolders of `wiki/` are not included by the current lister.

### Ingest

```bash
llm-wiki ingest path/to/sample-paper.md
llm-wiki ingest path/to/folder --no-summarize
```

- Directory ingest is recursive. Each file is copied by its basename into `raw/`, not by its relative path.
- The original file outside the library is not modified.
- If that basename or note id already exists, the new copy is suffixed (`sample-paper-2`). The existing note is not rewritten.
- The manifest line records an absolute local path. Keep `work/` private.
- `--link-suggestions` writes `related` ids from keyword overlap. `--touch-related` refreshes summaries for those linked notes.

### Open

Resolution order:

1. An existing filesystem path is opened as given.
2. Otherwise `wiki/<argument>.md`.
3. Otherwise a note whose `id` matches.

If a file in the current directory has the same name as a note id, `open` uses that file. Exit code `4` means nothing resolved. Tests stub the opener; a normal run uses the system handler (Windows `os.startfile`, macOS `open`, Linux `xdg-open`).

### Summarize and query

`summarize` accepts `--mode local` only. Any other mode exits `2` with `Only local mode is currently implemented.` There is no cloud summarizer in this version.

`query` splits the question into terms longer than two characters, skips notes of type `query`, and prints summaries plus citations. It does not call a model. Without `--save` it does not write a note. A question with no usable terms exits `2`.

### Link and validation

```bash
llm-wiki link project-alpha example-research-note
llm-wiki link project-alpha example-research-note --relation cites --no-bidirectional
llm-wiki check --strict
llm-wiki lint
```

Linking the same pair again does not duplicate the id. `--relation` stores that frontmatter key. `check` validates `related`, not other relation keys. `--strict` requires `sources` to be a list. `http://`, `https://`, and `mailto:` links are not treated as broken files. `lint` exits `3` on structural errors and, in that case, does not print warnings. Warnings alone still exit `0`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success, including "no notes" or "no matches". |
| `2` | Invalid arguments, missing ingest input, or unsupported summarize mode. |
| `3` | `check` or `lint` found a structural problem. |
| `4` | Note id or path was not found. |

Exit code `1` is reserved for unexpected runtime failure. The commands above use `0`, `2`, `3`, and `4`.

## Synthetic examples

Docs and tests use stand-ins such as Project Alpha, Distributed Systems, Example Research Note, and Sample Paper. Do not put real personal or confidential notes in this framework repository.
