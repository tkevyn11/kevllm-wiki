# kevllm-wiki

**A local-first, CLI-first framework for turning documents into a private Markdown knowledge base.**

kevllm-wiki keeps **Markdown + YAML frontmatter as the long-term source of truth**, while adding quality-gated document extraction, optional local OCR, explicit human review, local search, linking, validation, and rebuildable derived outputs.

> **Current release:** `v0.2.0`  
> **Status:** Generic Framework MVP — **COMPLETE**  
> **License:** MIT

[Release notes](docs/RELEASE_NOTES_v0.2.0.md) · [Quickstart](docs/QUICKSTART.md) · [User guide](docs/USER_GUIDE.md) · [Architecture](docs/ARCHITECTURE.md) · [Privacy](docs/PRIVACY.md)

---

## What it does

kevllm-wiki provides a lightweight workflow for building and maintaining a local knowledge library without requiring a database, hosted vector store, or cloud LLM.

### Core capabilities

- **Local-first knowledge base** — canonical notes remain ordinary Markdown files.
- **CLI-first workflow** — initialize, ingest, list, search, open, summarize, link, validate, query, lint, and review from the terminal.
- **Quality-gated extraction** — extracts readable text from Markdown/text, PDF, DOCX, and PPTX sources.
- **Optional local OCR** — supports standalone images and scanned PDFs through an optional PaddleOCR backend.
- **Human review workflow** — low-confidence extracts stay non-canonical until explicitly approved.
- **Nested notes** — organize `wiki/` into folders without losing search, validation, or linking.
- **Portable provenance** — derived manifests use relative paths and content hashes rather than machine-specific absolute paths.
- **Privacy-aware by design** — source files, user notes, temporary work, derived indexes, credentials, and OCR output are kept out of the framework's Git history.

---

## Design philosophy

The framework separates canonical knowledge from source material and rebuildable processing artifacts:

```text
source documents
      ↓
    raw/
      ↓
detect → extract → quality gate → optional OCR
      ↓
  derived/
      ↓
 clean ───────────────────────→ wiki/
 review → human review
              ├─ approve ─────→ wiki/
              └─ reject
```

### Workspace layers

| Layer | Purpose |
| --- | --- |
| `raw/` | Original source material and provenance copies |
| `wiki/` | **Canonical** Markdown + YAML knowledge base |
| `work/` | Transient processing state |
| `derived/` | Rebuildable extraction, graph, vector, or semantic outputs |
| `schema/` | Note and workflow conventions |

Deleting `derived/` must never destroy canonical knowledge.

---

## Quickstart

Clone/install the framework, then create your knowledge workspace in a **separate directory**.

```bash
git clone https://github.com/tkevyn11/kevllm-wiki.git
cd kevllm-wiki
python -m pip install -e .
```

Create a workspace:

```bash
mkdir my-knowledge
cd my-knowledge
llm-wiki init
```

Ingest and explore:

```bash
llm-wiki ingest path/to/sample-paper.md --extract
llm-wiki list
llm-wiki search "distributed systems"
llm-wiki check
llm-wiki lint
```

See the full [Quickstart](docs/QUICKSTART.md).

---

## Quality-gated ingestion

The original ingest behavior remains available:

```bash
llm-wiki ingest path/to/file
```

The v0.2 quality-gated path is opt-in:

```bash
llm-wiki ingest path/to/file --extract
```

Extraction results are classified as:

```text
clean
review
reject
ocr_needed
skip
error
```

Only `clean` content is promoted automatically into `wiki/`.

### Optional OCR

Install the OCR extras for image and scanned-PDF recognition:

```bash
python -m pip install -e ".[ocr]"
```

PaddlePaddle is installed separately according to the platform/CPU/GPU configuration described in [docs/EXTRACTION.md](docs/EXTRACTION.md).

Then run:

```bash
llm-wiki ingest scan.pdf --extract --ocr
```

OCR runs locally after the required models are available. First-time model setup may require network access; source documents are not uploaded to an OCR API.

---

## Human review

Items classified as `review` remain in `derived/` and do not become canonical notes automatically.

```bash
llm-wiki review list
llm-wiki review show <review-id>
llm-wiki review approve <review-id>
llm-wiki review reject <review-id>
```

Approval is explicit, provenance is preserved, and repeated/conflicting decisions are handled safely.

---

## CLI

The v0.2 command surface is:

```text
init
ingest
list
search
open
summarize
link
check
query
lint
review
```

See [docs/CLI_SPEC.md](docs/CLI_SPEC.md) for the command contract and exit-code behavior.

---

## Local-first does not mean "no AI"

The framework is intentionally useful **before** adding heavier AI infrastructure. Markdown remains canonical, while future retrieval, graph, vector, semantic, or agent layers can be generated from it as disposable/rebuildable representations.

Optional integrations must not replace the underlying knowledge files as the source of truth.

---

## Privacy model

User workspaces should live outside the framework repository.

The public Git repository intentionally excludes runtime/private data such as:

```text
raw/
wiki/
work/
derived/
.env
credentials
OCR output
generated indexes
local databases
IDE-specific state
```

Generated/derived data may contain fragments of source material, so it should be handled with the same privacy expectations as the original content.

See [docs/PRIVACY.md](docs/PRIVACY.md).

---

## Current scope

### v0.2.0 — Generic Framework MVP

Implemented:

- Markdown/YAML canonical note model
- local CLI workflow
- text/Markdown/PDF/DOCX/PPTX extraction
- quality gates
- optional image + scanned-PDF OCR
- explicit review/approval/rejection
- nested canonical notes
- portable derived manifests/events
- local keyword search and query
- linking, integrity checks, and linting
- safer framework/workspace separation
- CI, packaging, contribution, security, and release documentation

### Deferred / future

Intentionally outside the v0.2 MVP:

- OCR for image-only DOCX/PPTX
- MCP retrieval
- vector/semantic search
- GBrain/Semantica-style intelligence layers
- web or TUI interfaces
- cloud-hosted knowledge storage

See [docs/FUTURE_PHASE_2.md](docs/FUTURE_PHASE_2.md) and [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Optional integrations

The architecture can support tools that operate over the Markdown corpus without becoming canonical dependencies.

Examples include:

- Obsidian for browsing and graph visualization
- Graphify for rebuildable graph output under `derived/graphify/`
- Marp for presentations generated from selected Markdown notes
- Dataview for optional frontmatter-driven local views

---

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [User guide](docs/USER_GUIDE.md)
- [CLI specification](docs/CLI_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Extraction & OCR](docs/EXTRACTION.md)
- [Note schema](docs/NOTE_SCHEMA.md)
- [Folder structure](docs/FOLDER_STRUCTURE.md)
- [Privacy](docs/PRIVACY.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)
- [v0.2.0 release notes](docs/RELEASE_NOTES_v0.2.0.md)

---

## Development

Run the test suite:

```bash
pytest -q
```

The v0.2.0 release was validated with **90 passing tests**, package builds, clean-wheel installation, CLI smoke testing, and GitHub Actions on Python 3.11 and 3.12.

---

## License

MIT. See [LICENSE](LICENSE).
