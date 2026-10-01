"""Local PaddleOCR adapter. The engine is imported only when OCR runs."""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
from typing import Any

from ..models import OcrOutput
from .base import OcrDependencyError, install_message


class PaddleOcrProvider:
    """Read images and scanned PDFs on this machine. No cloud OCR call."""

    name = "paddleocr"

    def __init__(self, engine: Any | None = None, pdf_opener: Any | None = None) -> None:
        self._engine = engine
        self._pdf_opener = pdf_opener

    def extract_image(self, path: Path) -> OcrOutput:
        text = "\n".join(texts_from_result(self._predict(path)))
        return OcrOutput(text=text, pages=1)

    def extract_pdf(self, path: Path) -> OcrOutput:
        opener = self._pdf_opener or open_pdf
        document = opener(Path(path))
        chunks: list[str] = []
        try:
            for index, page in enumerate(document, start=1):
                text = self._ocr_page(page)
                chunks.append(f"## Page {index}\n\n{text.strip()}")
        finally:
            close = getattr(document, "close", None)
            if callable(close):
                close()
        body = "\n\n".join(chunks)
        if body and not body.endswith("\n"):
            body += "\n"
        return OcrOutput(text=body, pages=len(chunks))

    def _ocr_page(self, page: Any) -> str:
        pixmap = page.get_pixmap(dpi=150)
        raw = pixmap.tobytes("png")
        with tempfile.TemporaryDirectory(prefix="llm-wiki-ocr-") as directory:
            image = Path(directory) / "page.png"
            image.write_bytes(raw)
            return "\n".join(texts_from_result(self._predict(image)))

    def _predict(self, path: Path) -> Any:
        engine = self._engine_or_create()
        if hasattr(engine, "predict"):
            return engine.predict(str(path))
        return engine.ocr(str(path))

    def _engine_or_create(self) -> Any:
        if self._engine is None:
            self._engine = build_engine()
        return self._engine


def load_paddle_provider() -> PaddleOcrProvider:
    """Return a provider after checking imports. Does not download models."""
    missing = [name for name in ("paddleocr", "paddle", "fitz") if importlib.util.find_spec(name) is None]
    if missing:
        raise OcrDependencyError(install_message(missing))
    return PaddleOcrProvider()


def open_pdf(path: Path) -> Any:
    try:
        import fitz
    except ImportError as exc:
        raise OcrDependencyError(install_message(["fitz"])) from exc
    return fitz.open(path)


def build_engine() -> Any:
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise OcrDependencyError(install_message(["paddleocr", "paddle"])) from exc
    settings = {
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
    }
    try:
        return PaddleOCR(engine="paddle", **settings)
    except TypeError:
        return PaddleOCR(**settings)


def texts_from_result(result: Any) -> list[str]:
    """Read recognized lines from a PaddleOCR 3.x or 2.x result."""
    lines: list[str] = []
    items = result if isinstance(result, list) else [result]
    for item in items:
        if item is None:
            continue
        recognized = _lookup(item, "rec_texts")
        if recognized:
            lines.extend(str(part).strip() for part in recognized if str(part).strip())
            continue
        if isinstance(item, list):
            for line in item:
                text = _legacy_line(line)
                if text:
                    lines.append(text)
    return lines


def _lookup(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _legacy_line(line: Any) -> str:
    if not isinstance(line, (list, tuple)) or len(line) < 2:
        return ""
    payload = line[1]
    if isinstance(payload, (list, tuple)) and payload:
        return str(payload[0]).strip()
    return ""
