"""File-type detection that does not trust extensions alone."""

from __future__ import annotations

from pathlib import Path


MARKDOWN_EXTENSIONS = {".md", ".markdown"}
TEXT_EXTENSIONS = {".txt", ".csv", ".tsv"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}

# Checked against the start of text-like files. Office packages are ZIP files,
# so these signatures are not applied to .docx or .pptx inputs.
_SIGNATURES = (
    (b"\xff\xd8\xff", "JPEG"),
    (b"JFIF", "JPEG"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"IHDR", "PNG"),
    (b"[Content_Types].xml", "OOXML"),
    (b"ppt/slides", "PPTX"),
    (b"PK\x03\x04", "ZIP"),
)


def file_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in MARKDOWN_EXTENSIONS:
        return "markdown"
    if suffix in TEXT_EXTENSIONS:
        return "text"
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".docx":
        return "docx"
    if suffix == ".pptx":
        return "pptx"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    return "unsupported"


def binary_signature(data: bytes) -> str:
    sample = data[:8192]
    for signature, name in _SIGNATURES:
        if signature in sample:
            return name
    return ""
