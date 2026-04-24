from __future__ import annotations

import datetime as dt
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
import yaml

RAW_DIR = "raw"
WIKI_DIR = "wiki"
WORK_DIR = "work"
DOCS_DIR = "docs"
SCHEMA_DIR = "schema"
INDEX_FILE = "index.md"
LOG_FILE = "log.md"
MANIFEST_FILE = "ingest-manifest.jsonl"
REQ_FIELDS = {"id", "title", "type", "created", "updated", "sources"}
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
EXIT_RUNTIME = 1
EXIT_ARGS = 2
EXIT_VALIDATION = 3
EXIT_NOT_FOUND = 4


@dataclass
class Note:
    path: Path
    fm: dict[str, Any]
    body: str


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def library_root(p: str | None) -> Path:
    return Path(p).resolve() if p else Path.cwd()


def read_note(path: Path) -> Note:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            fm_text = parts[0][4:]
            body = parts[1]
            try:
                fm = yaml.safe_load(fm_text) or {}
            except yaml.YAMLError:
                fm = {}
            return Note(path=path, fm=fm, body=body)
    return Note(path=path, fm={}, body=text)


def write_note(note: Note) -> None:
    fm_text = yaml.safe_dump(note.fm, sort_keys=False, allow_unicode=False).strip()
    content = f"---\n{fm_text}\n---\n\n{note.body.strip()}\n"
    note.path.write_text(content, encoding="utf-8")


def wiki_files(root: Path) -> list[Path]:
    wiki = root / WIKI_DIR
    if not wiki.exists():
        return []
    return sorted([p for p in wiki.glob("*.md") if p.name not in {INDEX_FILE, LOG_FILE}])


def resolve_note(root: Path, id_or_path: str) -> Note | None:
    p = Path(id_or_path)
    if p.exists():
        return read_note(p.resolve())
    candidate = root / WIKI_DIR / id_or_path
    if candidate.suffix != ".md":
        candidate = candidate.with_suffix(".md")
    if candidate.exists():
        return read_note(candidate)
    for wf in wiki_files(root):
        n = read_note(wf)
        if str(n.fm.get("id", "")) == id_or_path:
            return n
    return None


def ensure_structure(root: Path) -> None:
    for name in [RAW_DIR, WIKI_DIR, WORK_DIR, DOCS_DIR, SCHEMA_DIR]:
        (root / name).mkdir(parents=True, exist_ok=True)
    index = root / WIKI_DIR / INDEX_FILE
    if not index.exists():
        index.write_text("# Index\n\n", encoding="utf-8")
    log = root / WIKI_DIR / LOG_FILE
    if not log.exists():
        log.write_text("# Log\n\n", encoding="utf-8")
    schema_file = root / SCHEMA_DIR / "SCHEMA.md"
    if not schema_file.exists():
        schema_file.write_text(
            "# LLM-Wiki Schema\n\nDefines ingest/query/lint conventions for this library.\n",
            encoding="utf-8",
        )
    claude_schema = root / SCHEMA_DIR / "CLAUDE.md"
    if not claude_schema.exists():
        claude_schema.write_text(
            (
                "# LLM Wiki\n\n"
                "Maintainer contract for Karpathy-style wiki operations.\n\n"
                "- Keep raw immutable.\n"
                "- Keep wiki as canonical markdown knowledge base.\n"
                "- Keep index/log updated after wiki changes.\n"
            ),
            encoding="utf-8",
        )


def append_log(root: Path, kind: str, message: str) -> None:
    log = root / WIKI_DIR / LOG_FILE
    stamp = dt.datetime.now().strftime("%Y-%m-%d")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"## [{stamp}] {kind}\n- {message}\n\n")


def maybe_read_text(path: Path, max_chars: int = 4000) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".rst", ".py", ".json", ".yaml", ".yml"}:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
        except OSError:
            return ""
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore

            # Malformed xrefs in real-world PDFs spam stderr; pypdf still reads text.
            logging.getLogger("pypdf").setLevel(logging.ERROR)
            reader = PdfReader(str(path))
            chunks: list[str] = []
            for page in reader.pages[:20]:
                chunks.append((page.extract_text() or "").strip())
                if sum(len(c) for c in chunks) >= max_chars:
                    break
            return "\n".join(c for c in chunks if c)[:max_chars]
        except Exception:
            return ""
    if suffix == ".docx":
        try:
            from docx import Document  # type: ignore

            doc = Document(str(path))
            txt = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return txt[:max_chars]
        except Exception:
            return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def fail(message: str, code: int) -> None:
    typer.echo(message)
    raise typer.Exit(code)
