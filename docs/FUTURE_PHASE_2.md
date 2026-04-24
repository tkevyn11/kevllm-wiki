# Future Phase 2: GBrain-Inspired Intelligence Layer

## Purpose

Phase 2 explores intelligence capabilities that build on top of the Phase 1 markdown corpus. Phase 2 is additive, optional, and subordinate to the core rule that markdown files remain the long-term source of truth.

## Phase Boundary

Phase 1 provides:

- stable filesystem structure
- structured markdown notes with frontmatter
- CLI workflows for ingest, retrieval, linking, and validation

Phase 2 may add:

- richer reasoning over the existing corpus
- improved retrieval quality and synthesis workflows
- optional automation layers around planning and insight extraction

Phase 2 does not replace or hide `wiki/` as canonical storage.

## Potential Directions (Research and Planning)

- Optional semantic indexing to improve retrieval over large corpora.
- Optional graph-like relationship views generated from markdown metadata and links.
- Optional agent-assisted workflows for deeper synthesis and maintenance.
- Optional richer summarization pipelines with domain-aware prompts.
- Optional memory lifecycle services (confidence, supersession, retention, consolidation).

These are future directions, not implementation commitments for Phase 1.

## Optional external tooling (Phase 2 evaluation)

When planning Phase 2, consider evaluating third-party tools **only as optional layers** on top of the markdown corpus. They are not part of Phase 1 and are listed here as reminders to revisit during intelligence-layer design.

| Tool | Reference | Why revisit in Phase 2 |
|------|-----------|-------------------------|
| **Graphify** | [safishamsi/graphify](https://github.com/safishamsi/graphify) | Turns folders of docs/code into a queryable knowledge graph and reports; relevant if you want graph-assisted navigation or retrieval beyond flat keyword search. |
| **Hyper-Extract** | [yifanfeng97/Hyper-Extract](https://github.com/yifanfeng97/Hyper-Extract) | LLM-oriented structured extraction (including graph/hypergraph-style outputs); relevant if you want richer entity and relation extraction from unstructured text, subject to cost, privacy, and maintenance trade-offs. |

Integration principles:

- Phase 1 `wiki/` markdown remains canonical; any graph or extracted structure is derived and rebuildable.
- Prefer opt-in pipelines and explicit exports (for example into `work/` or a dedicated Phase 2 cache) rather than silent mutation of notes.
- Compare against lighter options (manual frontmatter, `check`, optional PDF preprocessors) before committing to heavy extraction stacks.

## Memory Lifecycle Extension (Candidate)

The memory-focused extension is a valid next step after Phase 1, but it should be implemented as an additive layer, not as a replacement for the markdown wiki model.

Candidate capabilities:

- **Confidence scoring** on claims, strengthened by reinforcement and recency.
- **Supersession links** between old and new claims (`supersedes`, `superseded_by`).
- **Retention policy** that deprioritizes stale low-value observations over time.
- **Consolidation tiers** for promotion from raw observations to stable semantic patterns.

Implementation note:

- Phase 1 may remain "memory-ready" by keeping optional metadata fields in markdown frontmatter.
- Runtime services for lifecycle automation, contradiction resolution, and promotion logic remain Phase 2 work.

## Guardrails for Phase 2

- Preserve markdown and frontmatter compatibility.
- Keep local-first operation available as a baseline.
- Avoid introducing mandatory vendor lock-in.
- Keep CLI workflows functional even if optional intelligence components are disabled.

## Migration Strategy

1. Keep Phase 1 command contracts stable.
2. Add new capabilities behind explicit opt-in commands/flags.
3. Ensure any derived index can be rebuilt from `wiki/` and `raw/`.
4. Maintain backward compatibility with existing notes and links.

## Explicit Non-Commitments

This document does not commit to a specific:

- vector database
- graph database
- hosted platform
- autonomous agent architecture
- hybrid retrieval implementation details (BM25/vector/graph fusion)
- multi-agent sync and shared-memory governance model

Those choices remain open for future evaluation once Phase 1 is operational and validated.
