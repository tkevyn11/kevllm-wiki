"""Optional local OCR. Importing this package does not import PaddleOCR."""

from .base import OcrDependencyError
from .paddle import load_paddle_provider

__all__ = ["OcrDependencyError", "load_paddle_provider"]
