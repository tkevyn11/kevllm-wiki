# LLM-Wiki (Phase 1)

LLM-Wiki is a local-first, CLI-first personal knowledge library that keeps markdown files as the long-term source of truth. Phase 1 focuses on a narrow, practical workflow: initialize a library, ingest materials, create and maintain structured notes, and query the wiki from the terminal without introducing heavy infrastructure.

Karpathy-style layering is explicitly supported: `raw/` + `wiki/` + `schema/`, with transient `work/` and rebuildable `derived/`. User notes belong in a separate workspace, not in this Git history. See [docs/PRIVACY.md](docs/PRIVACY.md).

LLM maintainer rules are provided via `CLAUDE.md` (root) and `schema/CLAUDE.md`.

## Phase 1 Scope

- Markdown in `wiki/` is canonical. `raw/` stores source copies, `work/` is transient, and `derived/` is rebuildable output.
- CLI is the primary interface (`llm-wiki`).
- Search is local keyword search over markdown notes.
- Notes use markdown plus YAML frontmatter.
- No database, vector search, knowledge graph, or heavy UI in Phase 1.

## Current Stage

- Phase 1 core CLI is implemented.
- Current milestone: hardening and polish (tests, validation depth, and command UX refinement).
- Progress details are tracked in [docs/ROADMAP.md](docs/ROADMAP.md).

## Phase 2 Boundary

Phase 2 is intentionally separate and deferred. A future GBrain-inspired intelligence layer may be added on top of the Phase 1 markdown corpus, but it does not replace markdown files as source of truth. Candidate external tools to evaluate in Phase 2 (for example [Graphify](https://github.com/safishamsi/graphify), [Hyper-Extract](https://github.com/yifanfeng97/Hyper-Extract)) are noted in [docs/FUTURE_PHASE_2.md](docs/FUTURE_PHASE_2.md), not used in Phase 1.

See [docs/FUTURE_PHASE_2.md](docs/FUTURE_PHASE_2.md).

## Folder Philosophy

- `raw/`: source material and provenance copies. May be private.
- `wiki/`: canonical markdown knowledge base.
- `work/`: transient processing files and manifests.
- `derived/`: rebuildable graph, vector, semantic, and extraction outputs. Never canonical.
- `schema/`: workflow conventions and note schema contract.
- `docs/`: product, architecture, and specification documents.

## Optional Integrations (Phase 1 Compatible)

These are optional helpers that fit the Phase 1 architecture. They are not required dependencies and do not change markdown-as-source-of-truth.

- **Web clipper**: use any clipper to save web articles as markdown into `raw/`.
- **Local image downloads**: keep images under `raw/assets/` and reference them from notes.
- **Obsidian graph view**: optional visualization layer over `wiki/` files.
- **Marp**: optional presentation output from selected markdown notes.
- **Dataview**: optional frontmatter querying for local browsing/reporting.

## CLI Commands

- `init`
- `ingest`
- `list`
- `search`
- `open`
- `summarize`
- `link`
- `check`
- `query`
- `lint`

Details and the behavior locked by tests are in [docs/CLI_SPEC.md](docs/CLI_SPEC.md).

## Quickstart

Install this package, then initialize a separate folder:

```bash
pip install -e .
mkdir my-knowledge
cd my-knowledge
llm-wiki init
llm-wiki ingest path/to/sample-paper.md
llm-wiki list
llm-wiki search "distributed systems"
llm-wiki check
```

See [docs/QUICKSTART.md](docs/QUICKSTART.md).

## Documentation Map

- Product requirements: [docs/PRD.md](docs/PRD.md)
- Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)
- MVP boundaries: [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Tech choices: [docs/TECH_STACK.md](docs/TECH_STACK.md)
- Quick reference: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- User manual: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- CLI contract: [docs/CLI_SPEC.md](docs/CLI_SPEC.md)
- Note schema: [docs/NOTE_SCHEMA.md](docs/NOTE_SCHEMA.md)
- Ingest flow: [docs/INGEST_WORKFLOW.md](docs/INGEST_WORKFLOW.md)
- Folder structure: [docs/FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md)
- Decision record: [docs/DECISIONS.md](docs/DECISIONS.md)
- Release checklist: [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
- Privacy: [docs/PRIVACY.md](docs/PRIVACY.md)
- Extraction service (not wired to `ingest` yet): [docs/EXTRACTION.md](docs/EXTRACTION.md)
- Future phase: [docs/FUTURE_PHASE_2.md](docs/FUTURE_PHASE_2.md)
