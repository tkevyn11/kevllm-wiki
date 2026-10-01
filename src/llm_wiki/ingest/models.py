"""Portable result records for local extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


STATUSES = ("clean", "review", "reject", "ocr_needed", "skip", "error")


@dataclass(frozen=True)
class OcrOutput:
    """Text returned by a local OCR backend."""

    text: str
    pages: int


class OcrProvider(Protocol):
    """Local OCR hook. Called only when a caller supplies a provider."""

    name: str

    def extract_image(self, path: Path) -> OcrOutput:
        """Read text from one image."""

    def extract_pdf(self, path: Path) -> OcrOutput:
        """Read a PDF by rendering pages locally. Keep ``## Page N`` headings."""


@dataclass(frozen=True)
class ExtractionResult:
    relative_path: str
    file_type: str
    status: str
    action: str
    reason: str
    text_chars: int
    noise_ratio: float
    output_relative_path: str
    sha256: str
    ocr_used: bool = False
    ocr_provider: str = ""
    ocr_pages: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
