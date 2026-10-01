"""Quality-gated local extraction. ``llm-wiki ingest`` uses it with ``--extract``."""

from .manifest import extract_sources
from .models import OcrProvider, ExtractionResult

__all__ = ["ExtractionResult", "OcrProvider", "extract_sources"]
