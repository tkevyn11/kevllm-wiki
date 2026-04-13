# LLM-Wiki (Phase 1)

LLM-Wiki is a local-first, CLI-first personal knowledge library that keeps markdown files as the long-term source of truth. Phase 1 focuses on a narrow, practical workflow: initialize a library, ingest materials, create and maintain structured notes, and query the wiki from the terminal without introducing heavy infrastructure.

## Phase 1 Scope

- Markdown and filesystem are canonical (`raw/`, `wiki/`, `work/`, `docs/`).
- CLI is the primary interface (`llm-wiki`).
- Search is local keyword search over markdown notes.
- Notes use markdown plus YAML frontmatter.
- No database, vector search, knowledge graph, or heavy UI in Phase 1.

## Current Stage

- Phase 1 core CLI is implemented.
- Current milestone: hardening and polish (tests, validation depth, and command UX refinement).
- Progress details are tracked in [docs/ROADMAP.md](docs/ROADMAP.md).

## Phase 2 Boundary

Phase 2 is intentionally separate and deferred. A future GBrain-inspired intelligence layer may be added on top of the Phase 1 markdown corpus, but it does not replace markdown files as source of truth.

See [docs/FUTURE_PHASE_2.md](docs/FUTURE_PHASE_2.md).

## Folder Philosophy

- `raw/`: original source materials.
- `wiki/`: structured markdown knowledge base.
- `work/`: temporary processing files and manifests.
- `docs/`: product, architecture, and specification documents.

## Optional Integrations (Phase 1 Compatible)

These are optional helpers that fit the Phase 1 architecture. They are not required dependencies and do not change markdown-as-source-of-truth.

- **Web clipper**: use any clipper to save web articles as markdown into `raw/`.
- **Local image downloads**: keep images under `raw/assets/` and reference them from notes.
- **Obsidian graph view**: optional visualization layer over `wiki/` files.
- **Marp**: optional presentation output from selected markdown notes.
- **Dataview**: optional frontmatter querying for local browsing/reporting.

## Planned CLI Commands

- `init`
- `ingest`
- `list`
- `search`
- `open`
- `summarize`
- `link`
- `check`

Details are defined in [docs/CLI_SPEC.md](docs/CLI_SPEC.md).

## Conceptual Quickstart

After CLI implementation lands, the expected flow is:

1. `llm-wiki init`
2. `llm-wiki ingest <path-or-url>`
3. `llm-wiki list`
4. `llm-wiki search "<keyword>"`
5. `llm-wiki check`

## Documentation Map

- Product requirements: [docs/PRD.md](docs/PRD.md)
- Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)
- MVP boundaries: [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Tech choices: [docs/TECH_STACK.md](docs/TECH_STACK.md)
- CLI contract: [docs/CLI_SPEC.md](docs/CLI_SPEC.md)
- Note schema: [docs/NOTE_SCHEMA.md](docs/NOTE_SCHEMA.md)
- Ingest flow: [docs/INGEST_WORKFLOW.md](docs/INGEST_WORKFLOW.md)
- Folder structure: [docs/FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md)
- Decision record: [docs/DECISIONS.md](docs/DECISIONS.md)
- Release checklist: [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
- Future phase: [docs/FUTURE_PHASE_2.md](docs/FUTURE_PHASE_2.md)
