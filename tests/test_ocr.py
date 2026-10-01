"""Optional local OCR behind `llm-wiki ingest --extract --ocr`."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter
from typer.testing import CliRunner

from llm_wiki.cli import app
from llm_wiki.ingest import extract_sources


runner = CliRunner()
CLEAN = "Project Alpha keeps notes about distributed systems in plain markdown.\n"
UNICODE = "分布式系统会在多台机器之间复制状态，并在故障之后继续提供服务。\n"


class FakeOcr:
    name = "fake"

    def __init__(self, image: str = "", pdf: str = "", pages: int = 1, error: Exception | None = None) -> None:
        self.image = image
        self.pdf = pdf
        self.pages = pages
        self.error = error
        self.image_calls = 0
        self.pdf_calls = 0

    def extract_image(self, path: Path) -> SimpleNamespace:
        self.image_calls += 1
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.image, pages=1)

    def extract_pdf(self, path: Path) -> SimpleNamespace:
        self.pdf_calls += 1
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.pdf, pages=self.pages)


def _notes(root: Path) -> list[Path]:
    return [path for path in (root / "wiki").glob("*.md") if path.name not in {"index.md", "log.md"}]


def _init() -> None:
    assert runner.invoke(app, ["init", "-C", "."]).exit_code == 0


def _use(monkeypatch: pytest.MonkeyPatch, provider: FakeOcr) -> None:
    monkeypatch.setattr("llm_wiki.ingest.ocr.load_paddle_provider", lambda: provider)


def _png(path: Path) -> bytes:
    raw = b"\x89PNG\r\n\x1a\nIHDR"
    path.write_bytes(raw)
    return raw


def _blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)


def test_default_ingest_does_not_run_ocr() -> None:
    with runner.isolated_filesystem():
        _init()
        _png(Path("figure.png"))
        result = runner.invoke(app, ["ingest", "figure.png", "-C", "."])
        assert result.exit_code == 0, result.stdout
        assert Path("wiki/figure.md").exists()
        assert not Path("derived").exists()
        assert "OCR" not in result.stdout


def test_ocr_without_extract_is_rejected() -> None:
    with runner.isolated_filesystem():
        _init()
        _png(Path("figure.png"))
        result = runner.invoke(app, ["ingest", "figure.png", "-C", ".", "--ocr"])
        assert result.exit_code == 2, result.stdout
        assert "--extract" in result.stdout
        assert _notes(Path(".")) == []
        assert not Path("derived").exists()


def test_missing_ocr_backend_is_a_controlled_error() -> None:
    with runner.isolated_filesystem():
        _init()
        _png(Path("figure.png"))
        result = runner.invoke(app, ["ingest", "figure.png", "-C", ".", "--extract", "--ocr"])
        assert result.exit_code == 2, result.stdout
        assert "OCR support is not installed." in result.stdout
        assert 'pip install -e ".[ocr]"' in result.stdout
        assert "Traceback" not in result.stdout
        assert "Traceback" not in (result.stderr or "")
        assert _notes(Path(".")) == []


def test_fake_ocr_clean_image_creates_note(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeOcr(image=CLEAN)
    _use(monkeypatch, provider)
    with runner.isolated_filesystem():
        _init()
        raw = _png(Path("figure.png"))
        result = runner.invoke(app, ["ingest", "figure.png", "-C", ".", "--extract", "--ocr"])
        assert result.exit_code == 0, result.stdout
        assert "Clean: created note figure" in result.stdout
        note = Path("wiki/figure.md").read_text(encoding="utf-8")
        assert "Project Alpha keeps notes about distributed systems in plain markdown." in note
        assert "```" not in note
        assert "ocr_provider: fake" in note
        assert "ocr_used: true" in note
        assert Path("raw/figure.png").read_bytes() == raw
        extracted = list(Path("derived/extraction/text").rglob("*.md"))
        assert extracted
        assert "Project Alpha" in extracted[0].read_text(encoding="utf-8")
        portable = Path("derived/extraction/manifests/ingest.jsonl").read_text(encoding="utf-8")
        extraction = Path("derived/extraction/manifests/extraction.json").read_text(encoding="utf-8")
        assert str(Path(".").resolve()) not in portable
        assert str(Path(".").resolve()) not in extraction
        assert ":\\" not in portable
        event = json.loads(portable.splitlines()[0])
        assert event["ocr_used"] is True
        assert event["ocr_provider"] == "fake"
        assert event["ocr_pages"] == 1
        assert event["note_id"] == "figure"
        assert event["extraction_status"] == "clean"
    assert provider.image_calls == 1


def test_fake_ocr_review_image_does_not_create_note(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, FakeOcr(image="Hi\n"))
    with runner.isolated_filesystem():
        _init()
        _png(Path("figure.png"))
        result = runner.invoke(app, ["ingest", "figure.png", "-C", ".", "--extract", "--ocr"])
        assert result.exit_code == 0, result.stdout
        assert "requires review" in result.stdout
        assert _notes(Path(".")) == []
        extracted = list(Path("derived/extraction/text").rglob("*.md"))
        assert extracted
        assert "Hi" in extracted[0].read_text(encoding="utf-8")


def test_fake_ocr_failure_is_error_without_note(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(path: Path) -> SimpleNamespace:
        raise RuntimeError(f"ocr engine failed reading {path.resolve()}")

    provider = FakeOcr()
    provider.extract_image = boom  # type: ignore[method-assign]
    _use(monkeypatch, provider)
    with runner.isolated_filesystem():
        _init()
        raw = _png(Path("figure.png"))
        result = runner.invoke(app, ["ingest", "figure.png", "-C", ".", "--extract", "--ocr"])
        assert result.exit_code == 3, result.stdout
        assert "Error: figure.png" in result.stdout
        assert "ocr engine failed" in result.stdout
        assert _notes(Path(".")) == []
        assert Path("raw/figure.png").read_bytes() == raw
        extraction = Path("derived/extraction/manifests/extraction.json").read_text(encoding="utf-8")
        assert str(Path("figure.png").resolve()) not in extraction
        assert ":\\" not in extraction


def test_unicode_ocr_passes_quality_gate(tmp_path: Path) -> None:
    source = tmp_path / "figure.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\nIHDR")
    manifest = extract_sources(source, tmp_path / "out", ocr=FakeOcr(image=UNICODE))
    result = manifest["results"][0]
    assert result["status"] == "clean"
    assert result["ocr_used"] is True
    assert result["ocr_provider"] == "fake"
    raw = json.dumps(manifest)
    assert str(tmp_path) not in raw
    assert ":\\" not in raw
    text = (tmp_path / "out" / result["output_relative_path"]).read_text(encoding="utf-8")
    assert "分布式系统" in text


def test_noisy_ocr_text_is_reject(tmp_path: Path) -> None:
    source = tmp_path / "figure.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\nIHDR")
    noisy = "ok\u0001" * 40
    manifest = extract_sources(source, tmp_path / "out", ocr=FakeOcr(image=noisy))
    assert manifest["results"][0]["status"] == "reject"


def test_text_layer_pdf_does_not_call_ocr(tmp_path: Path) -> None:
    source = tmp_path / "sample-paper.pdf"
    content = b"BT /F1 12 Tf 72 720 Td (Sample Paper text layer.) Tj ET"
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
    source.write_bytes(header + b"".join(objects) + b"".join(xref) + trailer)
    provider = FakeOcr(pdf="this OCR text must not replace the text layer of Sample Paper.\n")
    manifest = extract_sources(source, tmp_path / "out", ocr=provider)
    assert manifest["results"][0]["status"] == "clean"
    assert manifest["results"][0]["ocr_used"] is False
    assert provider.pdf_calls == 0


def test_scanned_pdf_keeps_pages_and_gates_before_a_note(monkeypatch: pytest.MonkeyPatch) -> None:
    pages = (
        "## Page 1\n\nDistributed systems appear on the first scanned page of Sample Paper.\n\n"
        "## Page 2\n\nExample Research Note continues on the second scanned page.\n"
    )
    _use(monkeypatch, FakeOcr(pdf=pages, pages=2))
    with runner.isolated_filesystem():
        _init()
        _blank_pdf(Path("scan.pdf"))
        clean = runner.invoke(app, ["ingest", "scan.pdf", "-C", ".", "--extract", "--ocr"])
        assert clean.exit_code == 0, clean.stdout
        note = Path("wiki/scan.md").read_text(encoding="utf-8")
        assert note.index("## Page 1") < note.index("## Page 2")
        assert "Distributed systems appear on the first scanned page" in note
        event = json.loads(Path("derived/extraction/manifests/ingest.jsonl").read_text(encoding="utf-8"))
        assert event["ocr_pages"] == 2
        assert event["extraction_status"] == "clean"
        assert ":\\" not in json.dumps(event)

    _use(monkeypatch, FakeOcr(pdf="Hi\n", pages=1))
    with runner.isolated_filesystem():
        _init()
        _blank_pdf(Path("scan.pdf"))
        review = runner.invoke(app, ["ingest", "scan.pdf", "-C", ".", "--extract", "--ocr"])
        assert review.exit_code == 0, review.stdout
        assert "requires review" in review.stdout
        assert _notes(Path(".")) == []


def test_markdown_with_provider_does_not_call_ocr(tmp_path: Path) -> None:
    source = tmp_path / "project-alpha.md"
    source.write_text(CLEAN, encoding="utf-8")
    provider = FakeOcr(image="should not be used")
    manifest = extract_sources(source, tmp_path / "out", ocr=provider)
    assert manifest["results"][0]["status"] == "clean"
    assert provider.image_calls == 0
    assert manifest["results"][0]["ocr_used"] is False


def test_paddle_reports_missing_install_without_downloading() -> None:
    from llm_wiki.ingest.ocr import OcrDependencyError, load_paddle_provider

    with pytest.raises(OcrDependencyError) as caught:
        load_paddle_provider()
    message = str(caught.value)
    assert "OCR support is not installed." in message
    assert 'pip install -e ".[ocr]"' in message
    assert "paddlepaddle" in message


def test_paddle_pdf_pages_are_joined_from_local_images(tmp_path: Path) -> None:
    from llm_wiki.ingest.ocr.paddle import PaddleOcrProvider

    class Engine:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def predict(self, path: str) -> list[dict[str, list[str]]]:
            self.paths.append(path)
            number = len(self.paths)
            return [{"rec_texts": [f"Distributed systems page {number} readable text."]}]

    class Pix:
        def tobytes(self, fmt: str) -> bytes:
            assert fmt == "png"
            return b"png-bytes"

    class Page:
        def get_pixmap(self, dpi: int = 150) -> Pix:
            assert dpi == 150
            return Pix()

    class Doc:
        def __iter__(self):
            return iter([Page(), Page()])

        def close(self) -> None:
            self.closed = True

    opened: list[Path] = []

    def opener(path: Path) -> Doc:
        opened.append(path)
        return Doc()

    provider = PaddleOcrProvider(engine=Engine(), pdf_opener=opener)
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-1.4\n")
    output = provider.extract_pdf(source)
    assert output.pages == 2
    assert output.text.index("## Page 1") < output.text.index("## Page 2")
    assert "Distributed systems page 1 readable text." in output.text
    assert "Distributed systems page 2 readable text." in output.text
    assert str(tmp_path.resolve()) not in output.text
    assert opened == [source]


def test_paddle_reads_recognition_lines() -> None:
    from llm_wiki.ingest.ocr.paddle import texts_from_result

    modern = [{"rec_texts": ["Alpha line", "Beta line"]}]
    legacy = [[(None, ("Legacy line", 0.9))]]
    assert texts_from_result(modern) == ["Alpha line", "Beta line"]
    assert texts_from_result(legacy) == ["Legacy line"]
