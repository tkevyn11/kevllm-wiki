"""Language-neutral text quality checks.

Thresholds count Unicode alphanumeric characters. They do not require
Latin letters or a particular language.
"""

from __future__ import annotations

from .detect import binary_signature

# Control/replacement share of the string above which text is rejected.
MAX_NOISE_RATIO = 0.02
# Alphanumeric characters required before an extract is treated as clean.
MIN_CLEAN_MEANINGFUL = 16
# Below this, a PDF/DOCX/PPTX extract is treated as having no text layer.
MIN_TEXT_LAYER = 8


def meaningful_count(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


def noise_ratio(text: str) -> float:
    if not text:
        return 1.0
    noisy = 0
    for char in text:
        if char in "\n\r\t":
            continue
        if ord(char) < 32 or char == "\ufffd":
            noisy += 1
    return noisy / len(text)


def assess_text(text: str, raw: bytes) -> tuple[str, str, float]:
    """Return status, reason, and noise ratio for already-decoded text."""
    signature = binary_signature(raw)
    ratio = noise_ratio(text)
    if signature:
        return "reject", f"binary signature detected: {signature}", ratio
    count = meaningful_count(text)
    if count == 0:
        if text.strip() and ratio > MAX_NOISE_RATIO:
            return "reject", f"high control or replacement character ratio: {ratio:.3f}", ratio
        return "reject", "empty output", ratio
    if ratio > MAX_NOISE_RATIO:
        return "reject", f"high control or replacement character ratio: {ratio:.3f}", ratio
    if count < MIN_CLEAN_MEANINGFUL:
        return "review", "short extraction", ratio
    return "clean", "passed text quality gate", ratio
