from pathlib import Path

import yaml
from typer.testing import CliRunner

from llm_wiki.cli import app
from llm_wiki.core import REQ_FIELDS


runner = CliRunner()


def test_cli_exposes_expected_command_set() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.stdout
    help_text = result.stdout
    for cmd in ["init", "ingest", "list", "search", "open", "summarize", "link", "check"]:
        assert cmd in help_text


def test_required_schema_fields_match_note_schema_doc() -> None:
    doc = Path("docs/NOTE_SCHEMA.md").read_text(encoding="utf-8")
    required = {"id", "title", "type", "created", "updated", "sources"}
    # Keep implementation and docs aligned on required keys.
    assert REQ_FIELDS == required
    for key in required:
        assert f"`{key}`" in doc


def test_note_schema_example_contains_required_fields() -> None:
    doc = Path("docs/NOTE_SCHEMA.md").read_text(encoding="utf-8")
    marker = "```markdown"
    start = doc.find(marker)
    assert start != -1
    end = doc.find("```", start + len(marker))
    assert end != -1
    block = doc[start + len(marker) : end].strip()
    parts = block.split("---")
    assert len(parts) >= 3
    fm = yaml.safe_load(parts[1])
    for key in REQ_FIELDS:
        assert key in fm
