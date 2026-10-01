# Privacy and Security

This repository is framework code for a local markdown wiki. It is not a place to store a real knowledge library.

## What belongs in Git

Commit framework source, tests, schema, and documentation. Public examples must be synthetic. Neutral names such as Project Alpha, Distributed Systems, Example Research Note, and Sample Paper are fine.

Do not commit:

- source documents, notes, or attachments from a real library
- ingest manifests, logs, or OCR text that quote those materials
- embeddings, graph exports, or other generated indexes
- `.env` files, API keys, tokens, passwords, private keys, or certificates

`.gitignore` ignores repo-root `raw/`, `wiki/`, `work/`, and `derived/`, plus `.env`, `.env.*` (except a future `.env.example`), common credential filenames, local databases, and editor state. Those rules do not replace judgment. A secret pasted into a tracked file is still a secret.

## Runtime data

| Path | Role | Privacy note |
|---|---|---|
| `raw/` | Source material and provenance inputs | May be private. Ingest does not modify the original file outside the library; it copies it here. |
| `wiki/` | Canonical Markdown and YAML | Treat notes as private if the sources were private. |
| `work/` | Transient processing state | `work/ingest-manifest.jsonl` stores the absolute local path of each input file. |
| `derived/` | Rebuildable graph, vector, semantic, and extraction outputs | Not canonical. Generated text and indexes can still contain fragments of source content. |

Deleting `derived/` or `work/` must not be the only copy of knowledge you care about. `wiki/` is the source of truth.

## Optional tools and cloud

Graphify, semantic indexes, MCP caches, and future cloud or LLM integrations are optional. They must not become the source of truth. Do not send library content to a network service unless you chose that command and understand what leaves the machine. The current `summarize` and `query` commands are local; they do not call a model.

## User libraries

Keep a user workspace in a separate folder from this framework checkout. See [USER_GUIDE.md](USER_GUIDE.md). That folder is your data. This Git repository should not track it.
