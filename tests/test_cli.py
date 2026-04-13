from pathlib import Path

from typer.testing import CliRunner

from llm_wiki import commands
from llm_wiki.cli import app


runner = CliRunner()


def test_init_creates_structure() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert Path("raw").exists()
        assert Path("wiki").exists()
        assert Path("work").exists()
        assert Path("docs").exists()
        assert Path("wiki/index.md").exists()
        assert Path("wiki/log.md").exists()


def test_init_is_idempotent() -> None:
    with runner.isolated_filesystem():
        first = runner.invoke(app, ["init", "-C", "."])
        second = runner.invoke(app, ["init", "-C", "."])
        assert first.exit_code == 0
        assert second.exit_code == 0


def test_ingest_list_search_and_check_pass() -> None:
    with runner.isolated_filesystem():
        Path("sample.md").write_text("# Sample\n\nPhase testing content.\n", encoding="utf-8")

        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0

        ingest = runner.invoke(app, ["ingest", "sample.md", "-C", "."])
        assert ingest.exit_code == 0, ingest.stdout
        assert Path("work/ingest-manifest.jsonl").exists()

        listed = runner.invoke(app, ["list", "-C", "."])
        assert listed.exit_code == 0, listed.stdout
        assert "sample" in listed.stdout.lower()

        searched = runner.invoke(app, ["search", "phase", "-C", "."])
        assert searched.exit_code == 0, searched.stdout
        assert "sample" in searched.stdout.lower()

        checked = runner.invoke(app, ["check", "-C", "."])
        assert checked.exit_code == 0, checked.stdout


def test_check_fails_on_broken_related_reference() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0

        note = Path("wiki/bad.md")
        note.write_text(
            """---
id: bad
title: Bad
type: source
created: 2026-01-01T00:00:00+00:00
updated: 2026-01-01T00:00:00+00:00
sources:
  - ref: raw/x.md
    kind: file
    ingested_at: 2026-01-01T00:00:00+00:00
related: [does-not-exist]
---

# Bad
""",
            encoding="utf-8",
        )

        checked = runner.invoke(app, ["check", "-C", "."])
        assert checked.exit_code == 3, checked.stdout
        assert "related id not found" in checked.stdout.lower()


def _write_note(path: Path, note_id: str, title: str, related: str = "") -> None:
    extra_related = f"related: [{related}]\n" if related else "related: []\n"
    path.write_text(
        (
            "---\n"
            f"id: {note_id}\n"
            f"title: {title}\n"
            "type: source\n"
            "created: 2026-01-01T00:00:00+00:00\n"
            "updated: 2026-01-01T00:00:00+00:00\n"
            "sources:\n"
            "  - ref: raw/x.md\n"
            "    kind: file\n"
            "    ingested_at: 2026-01-01T00:00:00+00:00\n"
            f"{extra_related}"
            "---\n\n"
            f"# {title}\n"
        ),
        encoding="utf-8",
    )


def test_link_bidirectional_updates_related() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/a.md"), "a", "A")
        _write_note(Path("wiki/b.md"), "b", "B")

        linked = runner.invoke(app, ["link", "a", "b", "-C", "."])
        assert linked.exit_code == 0, linked.stdout

        a_text = Path("wiki/a.md").read_text(encoding="utf-8")
        b_text = Path("wiki/b.md").read_text(encoding="utf-8")
        assert "related:\n- b" in a_text
        assert "related:\n- a" in b_text


def test_link_no_bidirectional_updates_one_side() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/a.md"), "a", "A")
        _write_note(Path("wiki/b.md"), "b", "B")

        linked = runner.invoke(app, ["link", "a", "b", "-C", ".", "--no-bidirectional"])
        assert linked.exit_code == 0, linked.stdout

        a_text = Path("wiki/a.md").read_text(encoding="utf-8")
        b_text = Path("wiki/b.md").read_text(encoding="utf-8")
        assert "related:\n- b" in a_text
        assert "related:\n- a" not in b_text


def test_summarize_local_and_nonlocal_modes() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/a.md"), "a", "A")
        Path("wiki/a.md").write_text(
            Path("wiki/a.md").read_text(encoding="utf-8")
            + "\nFirst line.\nSecond line.\nThird line.\n",
            encoding="utf-8",
        )
        local = runner.invoke(app, ["summarize", "a", "-C", "."])
        assert local.exit_code == 0, local.stdout
        assert "summary for a" in local.stdout.lower()

        nonlocal_mode = runner.invoke(app, ["summarize", "a", "-C", ".", "--mode", "llm"])
        assert nonlocal_mode.exit_code == 2
        assert "only local mode is currently implemented" in nonlocal_mode.stdout.lower()


def test_check_strict_fails_when_sources_not_list() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("wiki/bad.md").write_text(
            """---
id: bad
title: Bad
type: source
created: 2026-01-01T00:00:00+00:00
updated: 2026-01-01T00:00:00+00:00
sources: wrong-shape
related: []
---

# Bad
""",
            encoding="utf-8",
        )
        checked = runner.invoke(app, ["check", "-C", ".", "--strict"])
        assert checked.exit_code == 3, checked.stdout
        assert "sources must be a list" in checked.stdout.lower()


def test_open_by_id_uses_windows_startfile(monkeypatch) -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_note(Path("wiki/a.md"), "a", "A")

        opened: dict[str, str] = {}

        monkeypatch.setattr(commands.sys, "platform", "win32")
        monkeypatch.setattr(commands.os, "startfile", lambda p: opened.setdefault("path", p), raising=False)

        result = runner.invoke(app, ["open", "a", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert opened.get("path", "").endswith("a.md")


def test_ingest_missing_input_returns_args_exit_code() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        result = runner.invoke(app, ["ingest", "missing-file.md", "-C", "."])
        assert result.exit_code == 2
        assert "input not found" in result.stdout.lower()


def test_open_missing_note_returns_not_found_exit_code() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        result = runner.invoke(app, ["open", "missing-note", "-C", "."])
        assert result.exit_code == 4
        assert "target not found" in result.stdout.lower()
