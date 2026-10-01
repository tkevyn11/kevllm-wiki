"""Synthetic tests for the quality-gated extraction core.

This subsystem is not called by `llm-wiki ingest`.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from pypdf import PdfWriter

from llm_wiki.ingest import extract_sources


class _OcrMustNotRun:
    def extract_image(self, path: Path) -> str:
        raise AssertionError(f"OCR image hook was called for {path.name}")

    def extract_pdf(self, path: Path) -> str:
        raise AssertionError(f"OCR pdf hook was called for {path.name}")


def _result_map(manifest: dict) -> dict[str, dict]:
    return {item["relative_path"]: item for item in manifest["results"]}


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


def _write_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)


def _write_docx(path: Path, paragraph: str) -> None:
    import docx

    document = docx.Document()
    document.add_paragraph(paragraph)
    document.save(path)


def _slide_xml(text: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>"
        f"{text}"
        "</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
    )


def _write_pptx(path: Path, slides: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types></Types>',
        )
        for index, text in enumerate(slides, start=1):
            archive.writestr(f"ppt/slides/slide{index}.xml", _slide_xml(text))


def test_clean_markdown_and_plain_text_are_accepted(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    (source / "project-alpha.md").write_text(
        "Project Alpha keeps notes about distributed systems in plain markdown.\n",
        encoding="utf-8",
    )
    (source / "sample-paper.txt").write_text(
        "Sample Paper describes distributed systems for an example research note.\r\n",
        encoding="utf-8",
    )
    manifest = extract_sources(source, tmp_path / "derived" / "extraction")
    results = _result_map(manifest)
    assert results["project-alpha.md"]["status"] == "clean"
    assert results["project-alpha.md"]["file_type"] == "markdown"
    assert results["sample-paper.txt"]["status"] == "clean"
    assert results["sample-paper.txt"]["file_type"] == "text"
    text = (tmp_path / "derived" / "extraction" / results["sample-paper.txt"]["output_relative_path"]).read_text(
        encoding="utf-8"
    )
    assert "\r" not in text
    assert "Sample Paper" in text


def test_unicode_text_is_not_rejected(tmp_path: Path) -> None:
    source = tmp_path / "notes.md"
    source.write_text(
        "分布式系统会在多台机器之间复制状态，并在故障之后继续提供服务。\n"
        "Sistem teragih menyimpan salinan data pada beberapa mesin dan pulih selepas kegagalan.\n",
        encoding="utf-8",
    )
    manifest = extract_sources(source, tmp_path / "out")
    result = manifest["results"][0]
    assert result["status"] in {"clean", "review"}
    assert result["status"] != "reject"
    written = (tmp_path / "out" / result["output_relative_path"]).read_text(encoding="utf-8")
    assert "分布式系统" in written
    assert "Sistem teragih" in written


def test_binary_disguised_as_markdown_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    (source / "photo.md").write_bytes(b"\xff\xd8\xff\xe0" + b"JFIF" + b"\x00" * 32)
    (source / "slides.md").write_bytes(b"PK\x03\x04[Content_Types].xml ppt/slides")
    manifest = extract_sources(source, tmp_path / "out")
    results = _result_map(manifest)
    assert results["photo.md"]["status"] == "reject"
    assert results["slides.md"]["status"] == "reject"
    assert "binary" in results["photo.md"]["reason"].lower()
    for item in manifest["results"]:
        if item["output_relative_path"]:
            assert item["output_relative_path"].startswith("rejected/")


def test_docx_and_pptx_extraction(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    _write_docx(source / "example-research-note.docx", "Example Research Note about distributed systems.")
    _write_pptx(
        source / "sample-paper.pptx",
        ["Distributed systems on slide one.", "Project Alpha on slide two."],
    )
    manifest = extract_sources(source, tmp_path / "out")
    results = _result_map(manifest)
    assert results["example-research-note.docx"]["status"] == "clean"
    docx_text = (tmp_path / "out" / results["example-research-note.docx"]["output_relative_path"]).read_text(
        encoding="utf-8"
    )
    assert "Example Research Note" in docx_text
    assert results["sample-paper.pptx"]["status"] == "clean"
    pptx_text = (tmp_path / "out" / results["sample-paper.pptx"]["output_relative_path"]).read_text(encoding="utf-8")
    assert "## Slide 1" in pptx_text
    assert "Distributed systems on slide one." in pptx_text
    assert "## Slide 2" in pptx_text
    assert "Project Alpha on slide two." in pptx_text
    assert pptx_text.index("## Slide 1") < pptx_text.index("## Slide 2")


def test_text_pdf_extracts_and_blank_pdf_needs_ocr(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    _write_text_pdf(source / "sample-paper.pdf", "Sample Paper text layer.")
    _write_blank_pdf(source / "scan.pdf")
    manifest = extract_sources(source, tmp_path / "out", ocr=_OcrMustNotRun())
    results = _result_map(manifest)
    assert results["sample-paper.pdf"]["status"] == "clean"
    pdf_text = (tmp_path / "out" / results["sample-paper.pdf"]["output_relative_path"]).read_text(encoding="utf-8")
    assert "Sample Paper text layer." in pdf_text
    assert results["scan.pdf"]["status"] == "ocr_needed"
    assert results["scan.pdf"]["output_relative_path"] == ""


def test_image_needs_ocr_and_unsupported_is_skipped(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    (source / "figure.png").write_bytes(b"\x89PNG\r\n\x1a\nIHDR")
    (source / "archive.bin").write_bytes(b"\x00\x01not-a-target")
    manifest = extract_sources(source, tmp_path / "out", ocr=_OcrMustNotRun())
    results = _result_map(manifest)
    assert results["figure.png"]["status"] == "ocr_needed"
    assert results["figure.png"]["file_type"] == "image"
    assert results["archive.bin"]["status"] == "skip"
    assert results["archive.bin"]["file_type"] == "unsupported"


def test_corrupt_docx_is_error_or_reject(tmp_path: Path) -> None:
    source = tmp_path / "broken.docx"
    source.write_bytes(b"this is not a word document")
    manifest = extract_sources(source, tmp_path / "out")
    assert manifest["results"][0]["status"] in {"error", "reject"}


def test_short_text_is_review_not_reject(tmp_path: Path) -> None:
    source = tmp_path / "short.txt"
    source.write_text("Hi\n", encoding="utf-8")
    manifest = extract_sources(source, tmp_path / "out")
    assert manifest["results"][0]["status"] == "review"


def test_output_paths_are_deterministic_and_collision_safe(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    (source / "Foo Bar.md").write_text(
        "Project Alpha keeps a longer note about distributed systems here.\n",
        encoding="utf-8",
    )
    (source / "foo-bar.md").write_text(
        "Example Research Note keeps another longer note about distributed systems.\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    first = extract_sources(source, output)
    second = extract_sources(source, output)
    first_paths = {item["relative_path"]: item["output_relative_path"] for item in first["results"]}
    second_paths = {item["relative_path"]: item["output_relative_path"] for item in second["results"]}
    assert first_paths == second_paths
    assert first_paths["Foo Bar.md"] == "text/foo-bar.md"
    assert first_paths["foo-bar.md"] == "text/foo-bar-2.md"
    assert (output / "text" / "foo-bar.md").is_file()
    assert (output / "text" / "foo-bar-2.md").is_file()


def test_manifest_is_portable_and_counts_match(tmp_path: Path) -> None:
    source = tmp_path / "sources"
    source.mkdir()
    marker = "MARKER-NOT-IN-MANIFEST"
    (source / "project-alpha.md").write_text(
        f"Project Alpha studies distributed systems. {marker}.\n",
        encoding="utf-8",
    )
    (source / "figure.jpg").write_bytes(b"\xff\xd8\xff\xe0JFIF")
    (source / "other.xyz").write_text("nope", encoding="utf-8")
    output = tmp_path / "derived" / "extraction"
    manifest = extract_sources(source, output)
    payload = json.loads((output / "manifests" / "extraction.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["created_at"]
    assert payload["counts"]["clean"] == 1
    assert payload["counts"]["ocr_needed"] == 1
    assert payload["counts"]["skip"] == 1
    assert sum(payload["counts"].values()) == 3
    raw = json.dumps(payload)
    assert marker not in raw
    assert str(tmp_path) not in raw
    assert ":\\" not in raw
    assert "C:/" not in raw
    for item in payload["results"]:
        assert item["sha256"]
        assert not Path(item["relative_path"]).is_absolute()
        assert "output_relative_path" in item
