# Product Requirements Document (Phase 1)

## Overview

Phase 1 defines a minimal, maintainable personal knowledge library where markdown files on local disk are the canonical data model. The system is designed for a solo builder and optimized for terminal workflows.

## Problem Statement

Personal research material often ends up fragmented across files and folders with inconsistent structure. Existing solutions are either too manual or too heavy for a local-first workflow. This project provides a lightweight CLI that turns local source materials into structured, searchable wiki notes without introducing a database or large UI surface.

## Target User

- Solo builder maintaining a personal knowledge corpus.
- Comfortable with filesystem and terminal tools.
- Wants transparent, editable files over opaque storage.

## Goals

- Keep markdown/filesystem as source of truth.
- Provide a CLI-first workflow for core knowledge operations.
- Standardize note metadata and source attribution.
- Support manual editing and long-term maintainability.
- Keep architecture simple enough to inspect and extend.

## Non-Goals (Phase 1)

- Building a full Obsidian replacement.
- Team collaboration workflows and permissions.
- Cloud sync, hosted services, or remote storage defaults.
- Vector search, pgvector, knowledge graph pipelines, or agent-memory infrastructure.
- Rich frontend application development.

## Core Functional Requirements

### FR-1: Initialize Library

- Command: `llm-wiki init`
- Creates `raw/`, `wiki/`, `work/`, and `docs/` if missing.
- Generates minimal starter files:
  - `wiki/index.md`
  - `wiki/log.md`
- Must be safe to re-run (idempotent).

### FR-2: Ingest Raw Materials

- Command: `llm-wiki ingest <input>`
- Supports local file and directory inputs in Phase 1.
- Captures ingest manifest entries in `work/`.
- Records source attribution in resulting notes.
- Never mutates original source files.

### FR-3: Create Structured Notes

- Generated notes must be markdown with YAML frontmatter.
- Required metadata fields must be present.
- Body remains manually editable at all times.
- Internal links must be standard markdown relative links.

### FR-4: List Notes

- Command: `llm-wiki list`
- Lists notes from `wiki/` with key metadata (title, id, type, updated).
- Supports basic filtering and a machine-readable JSON output mode.

### FR-5: Search Notes

- Command: `llm-wiki search "<query>"`
- Performs local keyword search over note title, metadata, and body.
- Returns ranked matches with file path and short snippet.

### FR-6: Open Notes

- Command: `llm-wiki open <id-or-path>`
- Opens note in default system editor/viewer.
- Supports resolution by note id and direct path.

### FR-7: Summarize Content

- Command: `llm-wiki summarize <id-or-path>`
- Default Phase 1 behavior is local heuristic summarization.
- Optional LLM-backed summarization may be enabled via config/environment.
- Core usage remains functional without cloud dependencies.

### FR-8: Validate Library Consistency

- Command: `llm-wiki check`
- Validates frontmatter schema compliance.
- Detects broken internal links.
- Detects missing required metadata and duplicate note ids.

## Quality Requirements

- Local-first behavior by default.
- Predictable command output and exit codes.
- Readable implementation with small, modular components.
- Test coverage for schema parsing, search, ingest manifests, and checks.

## Constraints

- Phase 1 uses local filesystem storage only.
- No database assumed.
- No vector index or graph engine in implementation.

## Success Criteria (Phase 1)

- A user can initialize, ingest, list, search, open, summarize, and check a library entirely via CLI.
- All notes are valid markdown files with inspectable metadata.
- The system remains understandable for a solo maintainer.

## Implementation Status (Current)

- **Overall phase**: Phase 1.
- **Current milestone**: Milestone 6 completed.
- **Status summary**:
  - Core command surface is implemented (`init`, `ingest`, `list`, `search`, `open`, `summarize`, `link`, `check`).
  - Automated tests are implemented and passing for both core flows and key failure paths.
  - CLI error handling and stable exit code behavior are standardized.
  - Remaining work is optional maintenance/refactor work, not MVP blocking scope.

### Functional Requirement Progress

- FR-1 Initialize Library: Completed
- FR-2 Ingest Raw Materials: Completed
- FR-3 Create Structured Notes: Completed
- FR-4 List Notes: Completed
- FR-5 Search Notes: Completed
- FR-6 Open Notes: Completed
- FR-7 Summarize Content: Completed (local mode)
- FR-8 Validate Library Consistency: Completed
