"""Portable result records for local extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


STATUSES = ("clean", "review", "reject", "ocr_needed", "skip", "error")


class OcrProvider(Protocol):
    """Future OCR hook. The Stage 3 pipeline accepts this and does not call it."""

    def extract_image(self, path: Path) -> str:
        """Read text from an image. Not used yet."""

    def extract_pdf(self, path: Path) -> str:
        """Read text from a PDF page image. Not used yet."""


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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
