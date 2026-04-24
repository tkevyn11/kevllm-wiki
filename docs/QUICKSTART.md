# LLM-Wiki Quickstart (One Page)

Use this if you want fast copy-paste commands.

## 1) Open PowerShell and go to project

```powershell
cd "D:\my LLM-wiki"
```

## 2) Check CLI is available

```powershell
llm-wiki --help
```

## 3) Initialize library (run once)

```powershell
llm-wiki init -C .
```

## 4) Ingest your first file

```powershell
llm-wiki ingest "C:\path\to\your\file.md" -C .
```

If your files are mostly PDF/DOC/PPT (recommended pattern):

```powershell
llm-wiki ingest "D:\my LLM-wiki\raw\processed" -C "D:\my LLM-wiki"
```

Use `raw\original\` for untouched originals and `raw\processed\` for extracted text/markdown.

## 5) See notes

```powershell
llm-wiki list
```

or with explicit library:

```powershell
llm-wiki list -C .
```

**Tip:** the library flag is **uppercase `-C`** (or `--library`). `llm-wiki list -c` fails with `No such option: -c`.

## 6) Search notes

```powershell
llm-wiki search "keyword"
```

## 7) Open note

Copy the **id** from `llm-wiki list` (one word, often with hyphens). Example:

```powershell
llm-wiki open acom-aneurysm
```

Do not type spaces inside the id (`open acom aneurysm` is wrong).

## 8) Summarize note

```powershell
llm-wiki summarize acom-aneurysm
```

## 9) Link two notes

```powershell
llm-wiki link note-a note-b
```

## 10) Check consistency

```powershell
llm-wiki check
```

Strict check:

```powershell
llm-wiki check --strict
```

## JSON outputs (optional)

```powershell
llm-wiki list --json
llm-wiki search "keyword" --json
```

## Typical daily sequence

```powershell
llm-wiki ingest "C:\path\to\new\notes" -C .
llm-wiki list
llm-wiki search "topic"
llm-wiki check
```

## If something fails

- `Input not found` -> file/folder path is wrong
- `Target not found` -> note id/path not found
- `Check failed` -> fix metadata or broken links in `wiki/`
- `No such option: -c` -> use **`-C`**, not `-c`
- `unexpected extra argument` -> `open`/`summarize` need **one** id; copy from `list`

For full beginner manual: [USER_GUIDE.md](USER_GUIDE.md)
