"""Quality-gated local extraction. Not used by ``llm-wiki ingest`` yet."""

from .manifest import extract_sources
from .models import OcrProvider, ExtractionResult

__all__ = ["ExtractionResult", "OcrProvider", "extract_sources"]
