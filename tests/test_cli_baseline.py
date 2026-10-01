"""Characterization tests for the committed public CLI baseline.

These tests lock behavior that already exists. They are not a redesign.
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from llm_wiki import commands
from llm_wiki.cli import app


runner = CliRunner()

_FRONTMATTER = """---
id: {note_id}
title: {title}
type: {note_type}
created: 2026-01-01T00:00:00+00:00
updated: 2026-01-01T00:00:00+00:00
sources:
  - ref: raw/synthetic.md
    kind: file
    ingested_at: 2026-01-01T00:00:00+00:00
tags: [{tags}]
related: []
---

# {title}
{body}
"""


def _write_note(
    path: Path,
    note_id: str,
    title: str,
    note_type: str = "source",
    tags: str = "",
    body: str = "Synthetic Source Document.",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _FRONTMATTER.format(
            note_id=note_id,
            title=title,
            note_type=note_type,
            tags=tags,
            body=body,
        ),
        encoding="utf-8",
    )


def test_help_lists_committed_command_surface() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.stdout
    for cmd in ["init", "ingest", "list", "search", "open", "summarize", "link", "check", "query", "lint"]:
        assert cmd in result.stdout


def test_init_rerun_preserves_existing_starter_content() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("wiki/index.md").write_text("# Index\n\nkept index sentinel\n", encoding="utf-8")
        Path("wiki/log.md").write_text("# Log\n\nkept log sentinel\n", encoding="utf-8")
        Path("schema/SCHEMA.md").write_text("kept schema sentinel\n", encoding="utf-8")

        again = runner.invoke(app, ["init", "-C", "."])
        assert again.exit_code == 0, again.stdout
        assert "kept index sentinel" in Path("wiki/index.md").read_text(encoding="utf-8")
        assert "kept log sentinel" in Path("wiki/log.md").read_text(encoding="utf-8")
        assert "kept schema sentinel" in Path("schema/SCHEMA.md").read_text(encoding="utf-8")


def test_ingest_directory_copies_basenames_and_updates_manifest_index_log() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("inbox/alpha.md").parent.mkdir(parents=True)
        Path("inbox/alpha.md").write_text(
            "Synthetic Source Document about distributed systems.\n",
            encoding="utf-8",
        )
        Path("inbox/nested").mkdir()
        Path("inbox/nested/beta.md").write_text(
            "Example Research Note for Project Alpha.\n",
            encoding="utf-8",
        )

        result = runner.invoke(app, ["ingest", "inbox", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert "Ingested 2 file(s)." in result.stdout

        assert Path("raw/alpha.md").read_text(encoding="utf-8") == Path("inbox/alpha.md").read_text(encoding="utf-8")
        assert Path("raw/beta.md").read_text(encoding="utf-8") == Path("inbox/nested/beta.md").read_text(encoding="utf-8")
        assert Path("wiki/alpha.md").exists()
        assert Path("wiki/beta.md").exists()
        assert "id: alpha" in Path("wiki/alpha.md").read_text(encoding="utf-8")
        assert "id: beta" in Path("wiki/beta.md").read_text(encoding="utf-8")

        manifest = Path("work/ingest-manifest.jsonl").read_text(encoding="utf-8").strip().splitlines()
        note_ids = {json.loads(line)["note_id"] for line in manifest}
        assert note_ids == {"alpha", "beta"}
        index = Path("wiki/index.md").read_text(encoding="utf-8")
        assert "(alpha.md)" in index
        assert "(beta.md)" in index
        log = Path("wiki/log.md").read_text(encoding="utf-8")
        assert "alpha.md -> alpha" in log
        assert "beta.md -> beta" in log


def test_reingest_creates_suffixed_raw_copy_and_note_id() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("project-alpha.md").write_text(
            "Synthetic Source Document about distributed systems.\n",
            encoding="utf-8",
        )
        first = runner.invoke(app, ["ingest", "project-alpha.md", "-C", "."])
        assert first.exit_code == 0, first.stdout
        original_note = Path("wiki/project-alpha.md").read_text(encoding="utf-8")

        second = runner.invoke(app, ["ingest", "project-alpha.md", "-C", "."])
        assert second.exit_code == 0, second.stdout
        assert Path("wiki/project-alpha.md").read_text(encoding="utf-8") == original_note
        collided = Path("wiki/project-alpha-2.md").read_text(encoding="utf-8")
        assert "id: project-alpha-2" in collided
        assert Path("raw/project-alpha.md").exists()
        assert Path("raw/project-alpha-2.md").read_text(encoding="utf-8") == Path("project-alpha.md").read_text(
            encoding="utf-8"
        )
        manifest = Path("work/ingest-manifest.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert [json.loads(line)["note_id"] for line in manifest] == ["project-alpha", "project-alpha-2"]


def test_list_filters_by_type_and_tag() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/alpha.md"), "alpha", "Project Alpha", note_type="concept", tags="distributed")
        _write_note(Path("wiki/beta.md"), "beta", "Example Research Note", note_type="source", tags="draft")

        by_type = runner.invoke(app, ["list", "-C", ".", "--type", "concept", "--json"])
        assert by_type.exit_code == 0, by_type.stdout
        type_ids = [item["id"] for item in json.loads(by_type.stdout)]
        assert type_ids == ["alpha"]

        by_tag = runner.invoke(app, ["list", "-C", ".", "--tag", "draft", "--json"])
        assert by_tag.exit_code == 0, by_tag.stdout
        tag_ids = [item["id"] for item in json.loads(by_tag.stdout)]
        assert tag_ids == ["beta"]

        empty = runner.invoke(app, ["list", "-C", ".", "--type", "missing"])
        assert empty.exit_code == 0, empty.stdout
        assert "No notes found." in empty.stdout


def test_search_is_case_insensitive_and_ranks_title_matches_higher() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(
            Path("wiki/alpha.md"),
            "alpha",
            "Project Alpha",
            body="Unrelated systems text.",
        )
        _write_note(
            Path("wiki/beta.md"),
            "beta",
            "Other Note",
            body="The project alpha design is documented here.",
        )

        result = runner.invoke(app, ["search", "PROJECT ALPHA", "-C", ".", "--json"])
        assert result.exit_code == 0, result.stdout
        hits = json.loads(result.stdout)
        assert [hit["id"] for hit in hits] == ["alpha", "beta"]
        assert hits[0]["score"] > hits[1]["score"]

        missing = runner.invoke(app, ["search", "absent-phrase", "-C", "."])
        assert missing.exit_code == 0, missing.stdout
        assert "No matches." in missing.stdout


def test_open_resolves_existing_path_before_note_id(monkeypatch) -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/project-alpha.md"), "project-alpha", "Project Alpha")
        Path("project-alpha").write_text("path sentinel\n", encoding="utf-8")
        opened: dict[str, str] = {}
        monkeypatch.setattr(commands.sys, "platform", "win32")
        monkeypatch.setattr(commands.os, "startfile", lambda p: opened.setdefault("path", p), raising=False)

        result = runner.invoke(app, ["open", "project-alpha", "-C", "."])
        assert result.exit_code == 0, result.stdout
        opened_path = Path(opened["path"])
        assert opened_path.name == "project-alpha"
        assert opened_path.parent == Path(".").resolve()


def test_open_by_id_uses_wiki_note_when_path_is_absent(monkeypatch) -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/project-alpha.md"), "project-alpha", "Project Alpha")
        opened: dict[str, str] = {}
        monkeypatch.setattr(commands.sys, "platform", "win32")
        monkeypatch.setattr(commands.os, "startfile", lambda p: opened.setdefault("path", p), raising=False)

        result = runner.invoke(app, ["open", "project-alpha", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert Path(opened["path"]) == Path("wiki/project-alpha.md").resolve()


def test_summarize_write_keeps_existing_body_sections() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(
            Path("wiki/alpha.md"),
            "alpha",
            "Project Alpha",
            body="Distributed systems replicate state.\n\n## Source\n\n- `raw/synthetic.md`\n",
        )
        result = runner.invoke(app, ["summarize", "alpha", "-C", ".", "--write"])
        assert result.exit_code == 0, result.stdout
        text = Path("wiki/alpha.md").read_text(encoding="utf-8")
        assert "## Summary" in text
        assert "## Source" in text
        assert "raw/synthetic.md" in text


def test_link_default_relation_is_idempotent_and_custom_relation_uses_its_key() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/alpha.md"), "alpha", "Project Alpha")
        _write_note(Path("wiki/beta.md"), "beta", "Example Research Note")

        first = runner.invoke(app, ["link", "alpha", "beta", "-C", "."])
        second = runner.invoke(app, ["link", "alpha", "beta", "-C", "."])
        assert first.exit_code == 0, first.stdout
        assert second.exit_code == 0, second.stdout
        alpha = Path("wiki/alpha.md").read_text(encoding="utf-8")
        assert alpha.count("\n- beta\n") == 1

        custom = runner.invoke(app, ["link", "alpha", "beta", "-C", ".", "--relation", "cites"])
        assert custom.exit_code == 0, custom.stdout
        alpha = Path("wiki/alpha.md").read_text(encoding="utf-8")
        assert "cites:" in alpha
        assert "\n- beta\n" in alpha.split("cites:", 1)[1]


def test_link_missing_note_returns_not_found() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/alpha.md"), "alpha", "Project Alpha")
        result = runner.invoke(app, ["link", "alpha", "missing-note", "-C", "."])
        assert result.exit_code == 4
        assert "not found" in result.stdout.lower()


def test_check_missing_fields_duplicate_ids_and_broken_links() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("wiki/bad.md").write_text(
            """---
id: bad
type: source
created: 2026-01-01T00:00:00+00:00
updated: 2026-01-01T00:00:00+00:00
sources: []
---

# Bad
""",
            encoding="utf-8",
        )
        missing = runner.invoke(app, ["check", "-C", "."])
        assert missing.exit_code == 3, missing.stdout
        assert "missing fields" in missing.stdout.lower()
        assert "title" in missing.stdout.lower()

    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/a.md"), "same-id", "Project Alpha")
        _write_note(Path("wiki/b.md"), "same-id", "Example Research Note")
        duplicated = runner.invoke(app, ["check", "-C", "."])
        assert duplicated.exit_code == 3, duplicated.stdout
        assert "duplicate id: same-id in b.md and a.md" in duplicated.stdout

    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(
            Path("wiki/alpha.md"),
            "alpha",
            "Project Alpha",
            body="See [missing](missing-page.md) and [docs](https://example.com/spec).\n",
        )
        broken = runner.invoke(app, ["check", "-C", "."])
        assert broken.exit_code == 3, broken.stdout
        assert "broken link -> missing-page.md" in broken.stdout
        assert "example.com" not in broken.stdout.lower()


def test_query_prints_citations_without_saving_and_rejects_short_terms() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("project-alpha.md").write_text(
            "Distributed systems replicate state across machines.\n",
            encoding="utf-8",
        )
        assert runner.invoke(app, ["ingest", "project-alpha.md", "-C", "."]).exit_code == 0
        result = runner.invoke(app, ["query", "distributed systems", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert "## Answer" in result.stdout
        assert "[project-alpha](" in result.stdout
        assert "project-alpha.md)" in result.stdout
        assert list(Path("wiki").glob("query-*.md")) == []

        short = runner.invoke(app, ["query", "ok", "-C", "."])
        assert short.exit_code == 2
        assert "searchable terms" in short.stdout.lower()


def test_query_ignores_existing_query_notes() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(
            Path("wiki/query-only.md"),
            "query-only",
            "Distributed Systems Query",
            note_type="query",
            body="Distributed systems appear only in this query note.\n",
        )
        result = runner.invoke(app, ["query", "distributed systems", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert "No relevant notes found." in result.stdout


def test_lint_warns_on_missing_summary_and_fails_structural_errors() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/alpha.md"), "alpha", "Project Alpha", body="Distributed systems replicate state.\n")
        warned = runner.invoke(app, ["lint", "-C", "."])
        assert warned.exit_code == 0, warned.stdout
        assert "missing summary section: alpha.md" in warned.stdout
        assert "orphan note" in warned.stdout.lower()

    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("wiki/bad.md").write_text(
            """---
id: bad
type: source
created: 2026-01-01T00:00:00+00:00
updated: 2026-01-01T00:00:00+00:00
sources: []
---

# Bad
""",
            encoding="utf-8",
        )
        failed = runner.invoke(app, ["lint", "-C", "."])
        assert failed.exit_code == 3, failed.stdout
        assert "Lint structural issues:" in failed.stdout
        assert "Lint warnings:" not in failed.stdout
