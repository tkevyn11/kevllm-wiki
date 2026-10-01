"""Shared OCR errors. No engine imports."""

from __future__ import annotations


class OcrDependencyError(RuntimeError):
    """The optional local OCR stack is not installed."""


def install_message(missing: list[str]) -> str:
    lines = [
        "OCR support is not installed.",
        "Install the optional OCR dependencies, then retry:",
        '    pip install -e ".[ocr]"',
    ]
    if any(name in missing for name in ("paddleocr", "paddle")):
        lines.extend(
            [
                "PaddleOCR also needs a local PaddlePaddle 3.x engine. It is not part of that extra.",
                "CPU example:",
                "    python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/",
                "GPU installs follow the PaddlePaddle install guide for the local machine.",
            ]
        )
    if "fitz" in missing:
        lines.append("Scanned PDFs also need PyMuPDF, which is included in the ocr extra.")
    lines.append("The first OCR run may download model weights. Source files are not uploaded.")
    return "\n".join(lines)
