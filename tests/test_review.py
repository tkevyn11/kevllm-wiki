"""Explicit review promotion. Pending extracts stay out of wiki/ until approve."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from llm_wiki.cli import app


runner = CliRunner()
SHORT = "Hi there.\n"
OTHER = "Yo.\n"
OCR_TEXT = "Scanned line.\n"


def _init() -> None:
    assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0


def _notes() -> list[Path]:
    return [path for path in Path("wiki").glob("*.md") if path.name not in {"index.md", "log.md"}]


def _review_id_from_list(stdout: str, source: str) -> str:
    for line in stdout.splitlines():
        if f"source={source}" in line:
            return line.split()[0]
    raise AssertionError(f"{source} not listed:\n{stdout}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_review_manifest(entry: dict, created_at: str = "2026-10-01T00:00:00+00:00") -> None:
    manifest = Path("derived/extraction/manifests")
    manifest.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at": created_at,
        "counts": {"review": 1},
        "results": [entry],
    }
    (manifest / "extraction.json").write_text(json.dumps(payload), encoding="utf-8")


def test_review_list_shows_only_unresolved_items() -> None:
    with runner.isolated_filesystem():
        _init()
        Path("batch").mkdir()
        Path("batch/clean.md").write_text(
            "Project Alpha keeps notes about distributed systems in plain markdown.\n",
            encoding="utf-8",
        )
        Path("batch/a.txt").write_text(SHORT, encoding="utf-8")
        Path("batch/b.txt").write_text(OTHER, encoding="utf-8")
        extracted = runner.invoke(app, ["ingest", "batch", "-C", ".", "--extract"])
        assert extracted.exit_code == 0, extracted.stdout
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        assert listed.exit_code == 0, listed.stdout
        assert "source=a.txt" in listed.stdout
        assert "source=b.txt" in listed.stdout
        assert "source=clean.md" not in listed.stdout
        assert "ocr=no" in listed.stdout
        first = _review_id_from_list(listed.stdout, "a.txt")
        approved = runner.invoke(app, ["review", "approve", first, "-C", "."])
        assert approved.exit_code == 0, approved.stdout
        again = runner.invoke(app, ["review", "list", "-C", "."])
        assert again.exit_code == 0, again.stdout
        assert "source=a.txt" not in again.stdout
        assert "source=b.txt" in again.stdout
        assert _review_id_from_list(again.stdout, "b.txt") != first


def test_review_list_empty_exits_0() -> None:
    with runner.isolated_filesystem():
        _init()
        result = runner.invoke(app, ["review", "list", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert result.stdout.strip() == "No pending review items."


def test_review_show_prints_text_without_absolute_paths() -> None:
    with runner.isolated_filesystem():
        _init()
        Path("short.txt").write_text(SHORT, encoding="utf-8")
        assert runner.invoke(app, ["ingest", "short.txt", "-C", ".", "--extract"]).exit_code == 0
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        review_id = _review_id_from_list(listed.stdout, "short.txt")
        shown = runner.invoke(app, ["review", "show", review_id, "-C", "."])
        assert shown.exit_code == 0, shown.stdout
        assert "source_relative: short.txt" in shown.stdout
        assert "status: review" in shown.stdout
        assert "Hi there." in shown.stdout
        assert str(Path(".").resolve()) not in shown.stdout
        assert ":\\" not in shown.stdout
        assert _notes() == []
        assert not Path("derived/extraction/manifests/review.jsonl").exists()


def test_review_approve_creates_one_note_and_is_idempotent() -> None:
    with runner.isolated_filesystem():
        _init()
        Path("short.txt").write_text(SHORT, encoding="utf-8")
        assert runner.invoke(app, ["ingest", "short.txt", "-C", ".", "--extract"]).exit_code == 0
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        review_id = _review_id_from_list(listed.stdout, "short.txt")
        approved = runner.invoke(app, ["review", "approve", review_id, "-C", "."])
        assert approved.exit_code == 0, approved.stdout
        assert "created note short" in approved.stdout
        notes = _notes()
        assert [path.name for path in notes] == ["short.md"]
        note = notes[0].read_text(encoding="utf-8")
        assert "Hi there." in note
        assert "```" not in note
        assert "extraction_status: reviewed" in note
        assert "source_file: raw/short.txt" in note
        digest = _sha256(Path("raw/short.txt"))
        assert digest in note
        event_path = Path("derived/extraction/manifests/review.jsonl")
        event_text = event_path.read_text(encoding="utf-8")
        assert str(Path(".").resolve()) not in event_text
        assert ":\\" not in event_text
        event = json.loads(event_text.splitlines()[0])
        assert event["schema_version"] == 1
        assert event["event"] == "review"
        assert event["review_id"] == review_id
        assert event["source_relative"] == "short.txt"
        assert event["source_sha256"] == digest
        assert event["decision"] == "approved"
        assert event["note_id"] == "short"
        assert event["timestamp"]
        assert Path("derived/extraction/text").exists()
        again = runner.invoke(app, ["review", "approve", review_id, "-C", "."])
        assert again.exit_code == 0, again.stdout
        assert "Already approved" in again.stdout
        assert [path.name for path in _notes()] == ["short.md"]
        assert len(event_path.read_text(encoding="utf-8").splitlines()) == 1


def test_review_reject_creates_no_note_and_repeat_is_safe() -> None:
    with runner.isolated_filesystem():
        _init()
        Path("short.txt").write_text(SHORT, encoding="utf-8")
        raw = Path("short.txt").read_bytes()
        assert runner.invoke(app, ["ingest", "short.txt", "-C", ".", "--extract"]).exit_code == 0
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        review_id = _review_id_from_list(listed.stdout, "short.txt")
        rejected = runner.invoke(app, ["review", "reject", review_id, "-C", "."])
        assert rejected.exit_code == 0, rejected.stdout
        assert "Rejected" in rejected.stdout
        assert _notes() == []
        assert Path("raw/short.txt").read_bytes() == raw
        event = json.loads(Path("derived/extraction/manifests/review.jsonl").read_text(encoding="utf-8"))
        assert event["decision"] == "rejected"
        assert event["note_id"] is None
        assert event["source_relative"] == "short.txt"
        assert ":\\" not in json.dumps(event)
        again = runner.invoke(app, ["review", "reject", review_id, "-C", "."])
        assert again.exit_code == 0, again.stdout
        assert "Already rejected" in again.stdout
        assert _notes() == []
        quiet = runner.invoke(app, ["review", "list", "-C", "."])
        assert quiet.stdout.strip() == "No pending review items."


def test_cannot_cross_approve_or_reject() -> None:
    with runner.isolated_filesystem():
        _init()
        Path("short.txt").write_text(SHORT, encoding="utf-8")
        assert runner.invoke(app, ["ingest", "short.txt", "-C", ".", "--extract"]).exit_code == 0
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        review_id = _review_id_from_list(listed.stdout, "short.txt")
        assert runner.invoke(app, ["review", "reject", review_id, "-C", "."]).exit_code == 0
        blocked = runner.invoke(app, ["review", "approve", review_id, "-C", "."])
        assert blocked.exit_code == 3, blocked.stdout
        assert _notes() == []

    with runner.isolated_filesystem():
        _init()
        Path("short.txt").write_text(SHORT, encoding="utf-8")
        assert runner.invoke(app, ["ingest", "short.txt", "-C", ".", "--extract"]).exit_code == 0
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        review_id = _review_id_from_list(listed.stdout, "short.txt")
        assert runner.invoke(app, ["review", "approve", review_id, "-C", "."]).exit_code == 0
        original = Path("wiki/short.md").read_text(encoding="utf-8")
        blocked = runner.invoke(app, ["review", "reject", review_id, "-C", "."])
        assert blocked.exit_code == 3, blocked.stdout
        assert Path("wiki/short.md").read_text(encoding="utf-8") == original


def test_missing_review_item_exits_4() -> None:
    with runner.isolated_filesystem():
        _init()
        shown = runner.invoke(app, ["review", "show", "missing-item", "-C", "."])
        approved = runner.invoke(app, ["review", "approve", "missing-item", "-C", "."])
        assert shown.exit_code == 4, shown.stdout
        assert approved.exit_code == 4, approved.stdout
        assert _notes() == []


def test_corrupt_and_mismatched_metadata_exit_3() -> None:
    with runner.isolated_filesystem():
        _init()
        manifest = Path("derived/extraction/manifests")
        manifest.mkdir(parents=True)
        (manifest / "extraction.json").write_text("{", encoding="utf-8")
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        assert listed.exit_code == 3, listed.stdout

    with runner.isolated_filesystem():
        _init()
        Path("short.txt").write_text(SHORT, encoding="utf-8")
        assert runner.invoke(app, ["ingest", "short.txt", "-C", ".", "--extract"]).exit_code == 0
        Path("raw/short.txt").write_bytes(b"tampered")
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        review_id = _review_id_from_list(listed.stdout, "short.txt")
        approved = runner.invoke(app, ["review", "approve", review_id, "-C", "."])
        assert approved.exit_code == 3, approved.stdout
        assert _notes() == []
        assert not Path("derived/extraction/manifests/review.jsonl").exists()

    with runner.isolated_filesystem():
        _init()
        Path("raw").mkdir(exist_ok=True)
        Path("raw/noise.txt").write_text("ok\n", encoding="utf-8")
        text_dir = Path("derived/extraction/text")
        text_dir.mkdir(parents=True)
        (text_dir / "noise.md").write_text("\u0001" * 40, encoding="utf-8")
        _write_review_manifest(
            {
                "relative_path": "noise.txt",
                "file_type": "text",
                "status": "review",
                "text_chars": 40,
                "output_relative_path": "text/noise.md",
                "sha256": _sha256(Path("raw/noise.txt")),
            }
        )
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        review_id = _review_id_from_list(listed.stdout, "noise.txt")
        refused = runner.invoke(app, ["review", "approve", review_id, "-C", "."])
        assert refused.exit_code == 3, refused.stdout
        assert _notes() == []


def test_ocr_review_item_can_be_approved() -> None:
    with runner.isolated_filesystem():
        _init()
        raw = b"\x89PNG\r\n\x1a\nIHDR"
        Path("raw").mkdir(exist_ok=True)
        Path("raw/figure.png").write_bytes(raw)
        text_dir = Path("derived/extraction/text")
        text_dir.mkdir(parents=True)
        (text_dir / "figure.md").write_text(OCR_TEXT, encoding="utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        _write_review_manifest(
            {
                "relative_path": "figure.png",
                "file_type": "image",
                "status": "review",
                "text_chars": len(OCR_TEXT),
                "output_relative_path": "text/figure.md",
                "sha256": digest,
                "ocr_used": True,
                "ocr_provider": "fake",
                "ocr_pages": 1,
            }
        )
        listed = runner.invoke(app, ["review", "list", "-C", "."])
        assert listed.exit_code == 0, listed.stdout
        assert "ocr=yes" in listed.stdout
        review_id = _review_id_from_list(listed.stdout, "figure.png")
        shown = runner.invoke(app, ["review", "show", review_id, "-C", "."])
        assert "ocr_used: true" in shown.stdout
        assert "ocr_provider: fake" in shown.stdout
        assert "Scanned line." in shown.stdout
        assert ":\\" not in shown.stdout
        approved = runner.invoke(app, ["review", "approve", review_id, "-C", "."])
        assert approved.exit_code == 0, approved.stdout
        note = Path("wiki/figure.md").read_text(encoding="utf-8")
        assert "Scanned line." in note
        assert "extraction_status: reviewed" in note
        assert "ocr_provider: fake" in note
        assert digest in note
