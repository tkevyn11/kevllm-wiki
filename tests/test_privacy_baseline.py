"""Locks the public privacy ignore rules and the documented command surface."""

from pathlib import Path


COMMANDS = (
    "init",
    "ingest",
    "list",
    "search",
    "open",
    "summarize",
    "link",
    "check",
    "query",
    "lint",
)

DOC_COMMAND_FILES = (
    "README.md",
    "docs/CLI_SPEC.md",
    "docs/USER_GUIDE.md",
    "docs/QUICKSTART.md",
)


def _ignore_rules(text: str) -> list[str]:
    rules: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        rules.append(stripped)
    return rules


def test_gitignore_covers_secrets_runtime_data_and_editor_state() -> None:
    rules = _ignore_rules(Path(".gitignore").read_text(encoding="utf-8"))
    for required in (
        ".env",
        ".env.*",
        "/raw/",
        "/wiki/",
        "/work/",
        "/derived/",
        ".vscode/",
        ".idea/",
        "credentials.json",
        "*.pem",
        "*.sqlite",
    ):
        assert required in rules
    assert "examples/" not in rules
    assert "/examples/" not in rules


def test_public_docs_name_every_cli_command() -> None:
    for name in DOC_COMMAND_FILES:
        text = Path(name).read_text(encoding="utf-8")
        for cmd in COMMANDS:
            assert cmd in text, f"{name} does not mention {cmd}"


def test_cli_spec_matches_characterized_behavior() -> None:
    text = Path("docs/CLI_SPEC.md").read_text(encoding="utf-8")
    assert "existing filesystem path" in text
    assert "Only local mode is currently implemented." in text
    assert "sample-paper-2" in text or "`project-alpha-2`" in text
    assert "does not duplicate the id" in text
    assert "type` is `query` are skipped" in text or "type `query` are skipped" in text
    assert "do not print warnings" in text
