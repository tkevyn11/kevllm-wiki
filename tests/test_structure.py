"""Nested canonical notes, Graphify output location, and init workspace guard."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from llm_wiki import commands
from llm_wiki.cli import app


runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]

_NOTE = """---
id: {note_id}
title: {title}
type: concept
created: 2026-01-01T00:00:00+00:00
updated: 2026-01-01T00:00:00+00:00
sources:
  - ref: raw/synthetic.md
    kind: file
    ingested_at: 2026-01-01T00:00:00+00:00
tags: []
related: {related}
---

# {title}

{body}
"""


def _init() -> None:
    assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0


def _write(relative: str, note_id: str, title: str, body: str, related: str = "[]") -> None:
    path = Path("wiki") / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _NOTE.format(note_id=note_id, title=title, body=body, related=related),
        encoding="utf-8",
    )


def test_nested_note_appears_in_list_with_relative_path() -> None:
    with runner.isolated_filesystem():
        _init()
        _write(
            "research/paper-a.md",
            "paper-a",
            "Sample Paper",
            "Project Alpha keeps notes about distributed systems.\n",
        )
        listed = runner.invoke(app, ["list", "-C", ".", "--json"])
        assert listed.exit_code == 0, listed.stdout
        payload = json.loads(listed.stdout)
        assert [item["id"] for item in payload] == ["paper-a"]
        assert payload[0]["path"] == "wiki/research/paper-a.md"
        assert ":\\" not in listed.stdout
        assert str(Path(".").resolve()) not in listed.stdout


def test_nested_note_is_searchable() -> None:
    with runner.isolated_filesystem():
        _init()
        _write(
            "research/paper-a.md",
            "paper-a",
            "Sample Paper",
            "Distributed systems appear in this nested research note.\n",
        )
        found = runner.invoke(app, ["search", "nested research", "-C", ".", "--json"])
        assert found.exit_code == 0, found.stdout
        payload = json.loads(found.stdout)
        assert payload[0]["id"] == "paper-a"
        assert payload[0]["path"] == "wiki/research/paper-a.md"
        assert ":\\" not in found.stdout


def test_nested_note_opens_by_id(monkeypatch) -> None:
    with runner.isolated_filesystem():
        _init()
        _write("research/paper-a.md", "paper-a", "Sample Paper", "A nested canonical note.\n")
        opened: dict[str, str] = {}
        monkeypatch.setattr(commands.sys, "platform", "win32")
        monkeypatch.setattr(commands.os, "startfile", lambda p: opened.setdefault("path", p), raising=False)
        result = runner.invoke(app, ["open", "paper-a", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert Path(opened["path"]) == Path("wiki/research/paper-a.md").resolve()
        assert "Opened wiki/research/paper-a.md" in result.stdout
        assert ":\\" not in result.stdout


def test_nested_note_is_queried() -> None:
    with runner.isolated_filesystem():
        _init()
        _write(
            "research/paper-a.md",
            "paper-a",
            "Sample Paper",
            "## Summary\n\nDistributed systems keep a nested note available to query.\n",
        )
        result = runner.invoke(app, ["query", "distributed systems", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert "[paper-a](wiki/research/paper-a.md)" in result.stdout
        assert ":\\" not in result.stdout
        assert str(Path(".").resolve()) not in result.stdout


def test_nested_note_participates_in_check() -> None:
    with runner.isolated_filesystem():
        _init()
        _write(
            "research/paper-a.md",
            "paper-a",
            "Sample Paper",
            "## Summary\n\nA complete nested note.\n",
        )
        passed = runner.invoke(app, ["check", "-C", "."])
        assert passed.exit_code == 0, passed.stdout
        assert "(1 notes)" in passed.stdout
        Path("wiki/research/paper-a.md").write_text("# no frontmatter\n", encoding="utf-8")
        failed = runner.invoke(app, ["check", "-C", "."])
        assert failed.exit_code == 3, failed.stdout
        assert "research/paper-a.md" in failed.stdout


def test_nested_note_participates_in_lint() -> None:
    with runner.isolated_filesystem():
        _init()
        _write("research/paper-a.md", "paper-a", "Sample Paper", "No summary section here.\n")
        warned = runner.invoke(app, ["lint", "-C", "."])
        assert warned.exit_code == 0, warned.stdout
        assert "(1 notes)" in warned.stdout
        assert "paper-a" in warned.stdout


def test_duplicate_ids_across_folders_are_detected() -> None:
    with runner.isolated_filesystem():
        _init()
        _write("projects/project-alpha.md", "same-id", "Project Alpha", "First copy.\n")
        _write("archive/old-project-alpha.md", "same-id", "Project Alpha", "Second copy.\n")
        checked = runner.invoke(app, ["check", "-C", "."])
        assert checked.exit_code == 3, checked.stdout
        assert "duplicate id: same-id" in checked.stdout
        assert "projects/project-alpha.md" in checked.stdout
        assert "archive/old-project-alpha.md" in checked.stdout
        linted = runner.invoke(app, ["lint", "-C", "."])
        assert linted.exit_code == 3, linted.stdout
        assert "duplicate id: same-id" in linted.stdout


def test_link_validation_sees_nested_notes() -> None:
    with runner.isolated_filesystem():
        _init()
        _write("concepts/alpha.md", "alpha", "Project Alpha", "## Summary\n\nAlpha note.\n")
        _write("archive/beta.md", "beta", "Example Research Note", "## Summary\n\nBeta note.\n")
        linked = runner.invoke(app, ["link", "alpha", "beta", "-C", "."])
        assert linked.exit_code == 0, linked.stdout
        checked = runner.invoke(app, ["check", "-C", "."])
        assert checked.exit_code == 0, checked.stdout
        assert "(2 notes)" in checked.stdout


def test_index_and_log_remain_excluded() -> None:
    with runner.isolated_filesystem():
        _init()
        Path("wiki/index.md").write_text("UNIQUEINDEXMARKER should not be a note.\n", encoding="utf-8")
        Path("wiki/log.md").write_text("UNIQUELOGMARKER should not be a note.\n", encoding="utf-8")
        listed = runner.invoke(app, ["list", "-C", "."])
        assert listed.exit_code == 0, listed.stdout
        assert "No notes found." in listed.stdout
        searched = runner.invoke(app, ["search", "UNIQUEINDEXMARKER", "-C", "."])
        assert searched.exit_code == 0, searched.stdout
        assert "No matches." in searched.stdout
        checked = runner.invoke(app, ["check", "-C", "."])
        assert checked.exit_code == 0, checked.stdout
        assert "(0 notes)" in checked.stdout


def test_graphify_docs_use_derived_graphify() -> None:
    targets = [
        REPO_ROOT / ".agents" / "skills" / "graphify" / "SKILL.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "schema" / "CLAUDE.md",
        REPO_ROOT / "schema" / "SCHEMA.md",
        REPO_ROOT / "docs" / "FOLDER_STRUCTURE.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "derived/graphify/" in text, path.name
    skill = (REPO_ROOT / ".agents" / "skills" / "graphify" / "SKILL.md").read_text(encoding="utf-8")
    header = skill.split("# /graphify", 1)[0]
    assert "cd` to the library `work/" not in header
    assert "outputs land in **`work/graphify-out/`" not in header
    assert "derived/graphify/" in header


def test_init_refuses_framework_checkout() -> None:
    result = runner.invoke(app, ["init", "-C", str(REPO_ROOT)])
    assert result.exit_code == 2, result.stdout
    assert "Refusing to initialize a user workspace inside the kevllm-wiki framework checkout." in result.stdout
    assert "Choose a separate directory." in result.stdout


def test_init_accepts_ordinary_workspace(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "other-tool"\n', encoding="utf-8")
    ordinary = runner.invoke(app, ["init", "-C", str(tmp_path)])
    assert ordinary.exit_code == 0, ordinary.stdout
    assert (tmp_path / "wiki" / "index.md").is_file()
    empty = tmp_path / "empty-library"
    empty.mkdir()
    created = runner.invoke(app, ["init", "-C", str(empty)])
    assert created.exit_code == 0, created.stdout
    assert (empty / "wiki" / "log.md").is_file()


def test_init_override_works_on_synthetic_checkout(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "llm-wiki"\n', encoding="utf-8")
    package = tmp_path / "src" / "llm_wiki"
    package.mkdir(parents=True)
    (package / "cli.py").write_text("", encoding="utf-8")
    refused = runner.invoke(app, ["init", "-C", str(tmp_path)])
    assert refused.exit_code == 2, refused.stdout
    assert not (tmp_path / "wiki").exists()
    allowed = runner.invoke(app, ["init", "-C", str(tmp_path), "--allow-framework-root"])
    assert allowed.exit_code == 0, allowed.stdout
    assert (tmp_path / "wiki" / "index.md").is_file()
