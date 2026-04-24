# LLM Wiki

A personal knowledge base maintained in the Karpathy LLM-Wiki pattern.

## Purpose

This wiki is a structured, interlinked knowledge base maintained by the LLM.
The human curates sources, asks questions, and guides analysis.

## Layer structure

```
raw/             -- source documents (immutable, never modify)
wiki/            -- markdown pages maintained by the LLM
wiki/index.md    -- content index / table of contents
wiki/log.md      -- append-only operation log
schema/          -- maintainer instructions and schema rules
```

## Ingest workflow

When the user asks to ingest new sources:

1. Read source material (or extracted text when available).
2. Create or update a source summary page in `wiki/`.
3. Create or update related concept/entity pages when relevant.
4. Add links between related pages.
5. Update `wiki/index.md` with one-line descriptions.
6. Append an operation entry to `wiki/log.md`.

Touching multiple pages per source is expected.

## Page format

Use markdown with frontmatter consistent with this project schema:

- required frontmatter: `id`, `title`, `type`, `created`, `updated`, `sources`
- optional: `tags`, `status`, `aliases`, `related`

Recommended body sections:

```markdown
# Title

## Summary

One to three concise paragraphs.

## Source

- `raw/path/to/source.ext`

## Related pages

- [related-page](related-page.md)
```

## Citation rules

- Keep source attribution in frontmatter `sources`.
- For factual claims, prefer explicit source mention in text where useful.
- If sources conflict, note contradiction explicitly.
- Mark uncertain claims clearly.

## Query workflow

When answering questions:

1. Read `wiki/index.md` first.
2. Read relevant pages and synthesize an answer.
3. Cite wiki pages used.
4. If useful, save the answer as a new query note.

## Graphify (optional)

When a **Graphify** graph exists under `work/graphify-out/`, you may use `GRAPH_REPORT.md` or `graph.json` for **navigation** (communities, cross-links, suggested questions). Do **not** treat the graph as a citation source; ground answers in `wiki/` notes and `raw/` sources. Invoke Graphify only when the user asks or via explicit `$graphify` in Codex; run pipeline steps from `work/` with inputs `../raw` and/or `../wiki` so outputs stay under `work/graphify-out/`.

## Lint workflow

During lint/audit:

- Check structural validity (schema, links, ids).
- Identify orphan notes and missing summaries.
- Flag potential contradictions or stale claims for human review.
- Report findings with actionable fixes.

## Rules

- Never modify files in `raw/`.
- Keep `wiki/index.md` and `wiki/log.md` updated after wiki changes.
- Keep note filenames lowercase with hyphens.
- Use clear, plain language.
- Ask the user when categorization is ambiguous.
