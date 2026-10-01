"""Local text extractors. No network and no OCR."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    chunks = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(chunk.strip() for chunk in chunks if chunk.strip())


def extract_docx(path: Path) -> str:
    import docx

    document = docx.Document(str(path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n\n".join(paragraphs)


def extract_pptx(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        for index, name in enumerate(names, start=1):
            root = ElementTree.fromstring(archive.read(name))
            texts = [node.text.strip() for node in root.iter() if node.text and node.text.strip()]
            body = "\n".join(texts)
            chunks.append(f"## Slide {index}\n\n{body}".rstrip())
    if not chunks:
        return ""
    return "\n\n".join(chunks) + "\n"
