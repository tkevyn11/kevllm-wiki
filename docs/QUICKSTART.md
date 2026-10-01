# LLM-Wiki Quickstart

Use a separate folder for your notes. This repository is the framework, not the library.

## 1) Install the framework

From the framework checkout:

```bash
python -m venv .venv
```

Activate it (`source .venv/bin/activate`, or `.venv\Scripts\Activate.ps1` on Windows), then:

```bash
pip install -e ".[dev]"
llm-wiki --help
```

Base use without the dev tools is `pip install -e .`. Optional local OCR is a separate extra, `pip install -e ".[ocr]"`, plus a local PaddlePaddle engine. It is not required for the commands below. See [EXTRACTION.md](EXTRACTION.md).

## 2) Create a workspace

```bash
mkdir my-knowledge
cd my-knowledge
llm-wiki init
```

`init` creates `raw/`, `wiki/`, `work/`, `docs/`, and `schema/`. Running it again does not overwrite starter files you have edited.

## 3) Ingest a local file

```bash
llm-wiki ingest path/to/sample-paper.md
llm-wiki list
llm-wiki search "distributed systems"
```

Ingest copies the file into `raw/` and writes a new note under `wiki/`. Ingesting the same filename again creates a suffixed copy such as `sample-paper-2`, and leaves the first note unchanged.

## 4) Open, summarize, link, check

```bash
llm-wiki open project-alpha
llm-wiki summarize project-alpha --write
llm-wiki link project-alpha example-research-note
llm-wiki check
llm-wiki lint
llm-wiki query "distributed systems"
```

`open` uses an existing filesystem path before a note id. `summarize` is local only. `query` prints a citation-backed answer from notes already in `wiki/`.

The library flag is uppercase `-C` / `--library`. `-c` is not accepted.

## If something fails

- Exit `2` and `Input not found`: the file or folder path is wrong.
- Exit `2` and `Only local mode is currently implemented`: `summarize --mode` was not `local`.
- Exit `4` and `Target not found`: the note id or path does not resolve.
- Exit `3` and `Check failed`: fix frontmatter, duplicate ids, or broken wiki links.

See [USER_GUIDE.md](USER_GUIDE.md), [CLI_SPEC.md](CLI_SPEC.md), and [PRIVACY.md](PRIVACY.md).
