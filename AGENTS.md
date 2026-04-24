# LLM-wiki — Codex / agent instructions

## Authoritative contract

Wiki maintenance rules live in **`schema/CLAUDE.md`** and **`schema/SCHEMA.md`**. Follow those for ingest, query, lint, frontmatter, and citations. This file orients Codex CLI; it does not override the schema.

## Hard rules

- Never modify files under **`raw/`**.
- Canonical notes live in **`wiki/`** (markdown + frontmatter). After wiki changes, update **`wiki/index.md`** and append **`wiki/log.md`**.
- **Graphify** outputs are **derived only** (navigation, structure, questions). Do not treat `work/graphify-out/` as a source of truth for factual claims; cite **`raw/`** and wiki notes instead.

## CLI

- Install: `pip install -e ".[dev]"` (from repo root).
- Entry point: **`llm-wiki`** — see `llm-wiki --help` or `python -m llm_wiki.cli --help` after install.
- Tests: `python -m pytest` (prefer over bare `pytest` if scripts are not on `PATH`).
- If Codex’s shell cannot find `python`, use the full path to your `python.exe` or fix Windows **PATH**, then restart Codex.

## Karpathy guidelines (repo skill)

Coding discipline (think first, minimal code, surgical diffs, verify goals) lives in the repo skill **`$karpathy-guidelines`**. It applies to **`src/`** and **`tests/`**; wiki maintenance still follows **`schema/CLAUDE.md`**. Upstream: [mbeijen/andrej-karpathy-skills-cursor-vscode](https://github.com/mbeijen/andrej-karpathy-skills-cursor-vscode).

## Graphify (optional)

- Install package: `pip install graphifyy` or `pip install -e ".[graphify]"`.
- In Codex, invoke the repo skill explicitly: **`$graphify`** (implicit invocation is disabled for this project).
- Run pipeline steps from **`work/`** so outputs land in **`work/graphify-out/`**; use input paths `../raw` and/or `../wiki` relative to `work/`.

## Superpowers (recommended)

[Superpowers](https://github.com/obra/superpowers) adds planning, verification, and systematic debugging skills. Use it for **implementation work** on this CLI and tooling (`src/`, `tests/`). It does **not** replace **`schema/CLAUDE.md`**: for **ingest, query, lint, and wiki edits**, that schema and this file’s hard rules still win.

**Install once** (registers in your Codex profile, not only this repo):

- **OpenAI Codex (CLI):** run **`/plugins`**, search **`superpowers`**, install the plugin.
- **OpenAI Codex (app):** Plugins in the sidebar → **Coding** → **Superpowers** → install.
- **Cursor:** in Agent chat, **`/add-plugin superpowers`**, or install “superpowers” from the plugin marketplace.

After install, Superpowers skills are available globally. By default they can **invoke implicitly** when your task matches each skill’s description; you can still call them explicitly (e.g. **`$brainstorming`**, **`$writing-plans`**, **`$verification-before-completion`**). This **`AGENTS.md`** file is the repo pointer: Codex merges it so those skills apply alongside project rules. See the upstream README for the full workflow list.

## Codex + existing `CLAUDE.md`

To keep the short root **`CLAUDE.md`** in the instruction chain, add to **`~/.codex/config.toml`**:

```toml
project_doc_fallback_filenames = ["CLAUDE.md"]
```

See [OpenAI Codex AGENTS.md discovery](https://developers.openai.com/codex/guides/agents-md/).
