"""Opt-in --extract ingest. Default ingest stays on the frozen path."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from llm_wiki.cli import app


runner = CliRunner()


def _write_text_pdf(path: Path, text: str) -> None:
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n",
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n",
        b"4 0 obj<</Length " + str(len(content)).encode() + b">>stream\n" + content + b"\nendstream\nendobj\n",
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n",
    ]
    header = b"%PDF-1.4\n"
    offsets: list[int] = []
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj)
    xref_pos = len(header) + sum(len(obj) for obj in objects)
    xref = [b"xref\n0 6\n", b"0000000000 65535 f \n"]
    xref.extend(f"{off:010d} 00000 n \n".encode() for off in offsets)
    trailer = f"trailer<</Size 6/Root 1 0 R>>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    path.write_bytes(header + b"".join(objects) + b"".join(xref) + trailer)


def _notes(root: Path) -> list[Path]:
    return [path for path in (root / "wiki").glob("*.md") if path.name not in {"index.md", "log.md"}]


def test_default_ingest_ignores_extraction_gate() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("short.txt").write_text("Hi\n", encoding="utf-8")
        result = runner.invoke(app, ["ingest", "short.txt", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert Path("wiki/short.md").exists()
        assert not Path("derived").exists()
        legacy = json.loads(Path("work/ingest-manifest.jsonl").read_text(encoding="utf-8"))
        assert legacy["event"] == "ingest"
        assert legacy["note_id"] == "short"
        assert Path(legacy["input"]).is_absolute()


def test_extract_clean_markdown_creates_note_and_preserves_raw(tmp_path: Path) -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        text = "Project Alpha keeps notes about distributed systems in plain markdown.\n"
        Path("project-alpha.md").write_text(text, encoding="utf-8")
        result = runner.invoke(app, ["ingest", "project-alpha.md", "-C", ".", "--extract"])
        assert result.exit_code == 0, result.stdout
        assert "Clean: created note project-alpha" in result.stdout
        note = Path("wiki/project-alpha.md").read_text(encoding="utf-8")
        assert "Project Alpha keeps notes about distributed systems in plain markdown." in note
        assert "extraction_status: clean" in note
        assert "source_file: raw/project-alpha.md" in note
        assert "source_sha256:" in note
        assert Path("raw/project-alpha.md").read_text(encoding="utf-8") == text
        assert Path("derived/extraction/text").exists()
        portable = Path("derived/extraction/manifests/ingest.jsonl").read_text(encoding="utf-8")
        extraction = Path("derived/extraction/manifests/extraction.json").read_text(encoding="utf-8")
        assert str(Path(".").resolve()) not in portable
        assert str(Path(".").resolve()) not in extraction
        assert ":\\" not in portable
        event = json.loads(portable.splitlines()[0])
        assert event["event"] == "extract"
        assert event["schema_version"] == 1
        assert event["source_relative"] == "project-alpha.md"
        assert event["raw_relative"] == "raw/project-alpha.md"
        assert event["note_id"] == "project-alpha"
        assert event["extraction_status"] == "clean"
        assert len(event["sha256"]) == 64


def test_extract_clean_pdf_creates_note_from_text_layer() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        _write_text_pdf(Path("sample-paper.pdf"), "Sample Paper text layer.")
        result = runner.invoke(app, ["ingest", "sample-paper.pdf", "-C", ".", "--extract"])
        assert result.exit_code == 0, result.stdout
        note = Path("wiki/sample-paper.md").read_text(encoding="utf-8")
        assert "Sample Paper text layer." in note
        assert "```" not in note


def test_extract_review_ocr_reject_skip_and_corrupt_create_no_notes() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        Path("short.txt").write_text("Hi\n", encoding="utf-8")
        review = runner.invoke(app, ["ingest", "short.txt", "-C", ".", "--extract"])
        assert review.exit_code == 0, review.stdout
        assert "requires review" in review.stdout
        assert _notes(Path(".")) == []

        Path("figure.png").write_bytes(b"\x89PNG\r\n\x1a\nIHDR")
        image = runner.invoke(app, ["ingest", "figure.png", "-C", ".", "--extract"])
        assert image.exit_code == 0, image.stdout
        assert "OCR needed: figure.png" in image.stdout
        assert "not enabled" in image.stdout
        assert _notes(Path(".")) == []

        Path("photo.md").write_bytes(b"\xff\xd8\xff\xe0JFIF" + b"\x00" * 16)
        rejected = runner.invoke(app, ["ingest", "photo.md", "-C", ".", "--extract"])
        assert rejected.exit_code == 3, rejected.stdout
        assert "Rejected: photo.md" in rejected.stdout
        assert _notes(Path(".")) == []

        Path("archive.bin").write_bytes(b"\x00\x01")
        skipped = runner.invoke(app, ["ingest", "archive.bin", "-C", ".", "--extract"])
        assert skipped.exit_code == 0, skipped.stdout
        assert "Skipped: archive.bin" in skipped.stdout
        assert _notes(Path(".")) == []

        Path("broken.docx").write_bytes(b"this is not a word document")
        corrupt = runner.invoke(app, ["ingest", "broken.docx", "-C", ".", "--extract"])
        assert corrupt.exit_code == 3, corrupt.stdout
        assert "Error: broken.docx" in corrupt.stdout
        assert _notes(Path(".")) == []
        assert Path("raw/broken.docx").read_bytes() == b"this is not a word document"


def test_extract_directory_keeps_distinct_raw_paths_and_continues_after_reject() -> None:
    with runner.isolated_filesystem():
        assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0
        long_text = "Project Alpha keeps notes about distributed systems in two folders.\n"
        Path("batch/a").mkdir(parents=True)
        Path("batch/b").mkdir(parents=True)
        Path("batch/a/note.md").write_text(long_text, encoding="utf-8")
        Path("batch/b/note.md").write_text(long_text, encoding="utf-8")
        Path("batch/short.txt").write_text("Hi\n", encoding="utf-8")
        Path("batch/figure.png").write_bytes(b"\x89PNG\r\n\x1a\nIHDR")
        Path("batch/photo.md").write_bytes(b"\xff\xd8\xff\xe0JFIF" + b"\x00" * 8)
        result = runner.invoke(app, ["ingest", "batch", "-C", ".", "--extract"])
        assert result.exit_code == 3, result.stdout
        assert "Clean: created note note" in result.stdout
        assert "Clean: created note note-2" in result.stdout
        assert Path("raw/a/note.md").read_text(encoding="utf-8") == long_text
        assert Path("raw/b/note.md").read_text(encoding="utf-8") == long_text
        assert Path("wiki/note.md").exists()
        assert Path("wiki/note-2.md").exists()
        assert not Path("wiki/short.md").exists()
        assert not Path("wiki/photo.md").exists()
        assert "clean=2" in result.stdout
        assert "review=1" in result.stdout
        assert "ocr_needed=1" in result.stdout
        assert "reject=1" in result.stdout
        portable = Path("derived/extraction/manifests/ingest.jsonl").read_text(encoding="utf-8")
        assert str(Path("batch").resolve()) not in portable
        assert ":\\" not in portable
        assert not Path("work/ingest-manifest.jsonl").exists()
