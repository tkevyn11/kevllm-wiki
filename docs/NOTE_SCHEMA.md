# Note Schema (Phase 1)

## Format

- File format: Markdown (`.md`)
- Metadata format: YAML frontmatter at top of file
- Body format: standard markdown, manually editable

## Required Frontmatter Fields

- `id`: stable unique note identifier (slug-like string)
- `title`: human-readable title
- `type`: note category (`source`, `concept`, `entity`, `summary`, `index`)
- `created`: ISO 8601 datetime
- `updated`: ISO 8601 datetime
- `sources`: list of source attribution objects

## Optional Frontmatter Fields

- `tags`: list of strings
- `status`: freeform lifecycle marker (for example: `draft`, `stable`)
- `aliases`: list of alternative names
- `related`: list of related note ids
- `attachments`: list of local asset paths (for example `raw/assets/...`)

## Source Attribution Schema

Each entry in `sources` should follow:

```yaml
sources:
  - ref: "raw/articles/example.md"
    kind: "file"
    ingested_at: "2026-04-13T20:00:00Z"
```

Allowed `kind` values in Phase 1:

- `file`
- `directory`
- `url`
- `manual`

## Linking Rules

- Primary internal link convention: relative markdown links.
  - Example: `[Transformer Notes](../wiki/transformer-notes.md)`
- `related` frontmatter supports relationship checks and CLI linking.
- `check` validates:
  - target file exists for internal markdown links
  - `related` ids resolve to existing notes

## Manual Editing Policy

- Users may edit frontmatter and body manually.
- CLI commands should preserve existing body text unless command intent requires updates.
- Frontmatter keys unknown to the schema should be preserved where possible (forward compatibility).

## Asset and Integration Notes

- Prefer local image references over remote URLs when feasible.
- Obsidian/Dataview-compatible fields are allowed as additional frontmatter, but Phase 1 CLI should not require Obsidian-specific syntax.

## Example Note

```markdown
---
id: transformer-attention
title: Transformer Attention
type: concept
created: 2026-04-13T20:00:00Z
updated: 2026-04-13T20:15:00Z
tags: [llm, architecture]
related: [self-attention, positional-encoding]
sources:
  - ref: raw/papers/attention-is-all-you-need.pdf
    kind: file
    ingested_at: 2026-04-13T20:00:00Z
---

# Transformer Attention

Attention allows each token to mix contextual information from other tokens through learned weights.
```
