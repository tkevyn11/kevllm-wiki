"""Run extraction and write rebuildable derived output plus a JSON manifest."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .detect import file_type_for
from .extract import extract_docx, extract_pdf, extract_pptx, normalize_text, read_text
from .models import STATUSES, ExtractionResult, OcrProvider
from .quality import MIN_TEXT_LAYER, assess_text, meaningful_count, noise_ratio


def extract_sources(
    source: Path,
    output_dir: Path,
    *,
    ocr: OcrProvider | None = None,
) -> dict[str, object]:
    """Extract ``source`` into ``output_dir``.

    ``ocr`` is reserved for a later stage and is not called.
    Results are not written to ``wiki/`` and source files are not modified.
    """
    del ocr  # extension point only
    source = Path(source)
    output_dir = Path(output_dir)
    root = source if source.is_dir() else source.parent
    files = sorted(_iter_files(source), key=lambda path: _portable_relative(path, root).casefold())
    used: set[str] = set()
    results = [_inspect(path, root, output_dir, used) for path in files]
    payload = _manifest_payload(results)
    manifest_path = output_dir / "manifests" / "extraction.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def _iter_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    return [path for path in source.rglob("*") if path.is_file()]


def _portable_relative(path: Path, root: Path) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        relative = Path(path.name)
    return relative.as_posix()


def _safe_stem(relative: str) -> str:
    parts: list[str] = []
    for part in Path(relative).with_suffix("").parts:
        cleaned = part.casefold()
        cleaned = re.sub(r"\s+", "-", cleaned)
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", cleaned)
        cleaned = cleaned.strip(".-") or "untitled"
        parts.append(cleaned)
    return "/".join(parts) if parts else "untitled"


def _allocate(used: set[str], bucket: str, relative: str) -> str:
    base = f"{bucket}/{_safe_stem(relative)}"
    candidate = f"{base}.md"
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}.md"
        index += 1
    used.add(candidate)
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _public_error(exc: Exception, path: Path) -> str:
    message = f"{type(exc).__name__}: {exc}"
    for piece in (str(path.resolve()), str(path)):
        if piece:
            message = message.replace(piece, path.name)
    message = re.sub(r"[A-Za-z]:\\[^\s'\"]+", path.name, message)
    message = re.sub(r"/(?:Users|home)/[^\s'\"]+", path.name, message)
    return message[:400]


def _write(output_dir: Path, relative_output: str, text: str) -> None:
    destination = output_dir / Path(relative_output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="\n")


def _result(
    relative: str,
    file_type: str,
    status: str,
    action: str,
    reason: str,
    text_chars: int,
    ratio: float,
    output_relative_path: str,
    digest: str,
) -> ExtractionResult:
    return ExtractionResult(
        relative_path=relative,
        file_type=file_type,
        status=status,
        action=action,
        reason=reason,
        text_chars=text_chars,
        noise_ratio=round(ratio, 6),
        output_relative_path=output_relative_path,
        sha256=digest,
    )


def _inspect(path: Path, root: Path, output_dir: Path, used: set[str]) -> ExtractionResult:
    relative = _portable_relative(path, root)
    file_type = file_type_for(path)
    digest = _sha256(path)
    raw = path.read_bytes()
    try:
        return _classify(path, relative, file_type, raw, digest, output_dir, used)
    except Exception as exc:
        return _result(relative, file_type, "error", "extract", _public_error(exc, path), 0, 1.0, "", digest)


def _classify(
    path: Path,
    relative: str,
    file_type: str,
    raw: bytes,
    digest: str,
    output_dir: Path,
    used: set[str],
) -> ExtractionResult:
    if file_type == "unsupported":
        return _result(relative, file_type, "skip", "none", "unsupported extension", 0, 1.0, "", digest)
    if file_type == "image":
        return _result(relative, file_type, "ocr_needed", "route_to_ocr", "image file requires OCR", 0, 1.0, "", digest)

    if file_type in {"markdown", "text"}:
        text = normalize_text(read_text(path))
        status, reason, ratio = assess_text(text, raw)
        action = "extract_text"
    elif file_type == "pdf":
        text = normalize_text(extract_pdf(path))
        action = "extract_pdf_text"
        if meaningful_count(text) < MIN_TEXT_LAYER:
            return _result(relative, file_type, "ocr_needed", "route_to_ocr", "no meaningful PDF text layer", 0, 1.0, "", digest)
        status, reason, ratio = assess_text(text, b"")
    elif file_type == "docx":
        text = normalize_text(extract_docx(path))
        action = "extract_docx_text"
        if meaningful_count(text) < MIN_TEXT_LAYER:
            return _result(relative, file_type, "ocr_needed", "route_to_ocr", "no textual document content", 0, 1.0, "", digest)
        status, reason, ratio = assess_text(text, b"")
    elif file_type == "pptx":
        text = normalize_text(extract_pptx(path))
        action = "extract_pptx_text"
        if meaningful_count(text) < MIN_TEXT_LAYER:
            return _result(relative, file_type, "ocr_needed", "route_to_ocr", "no structured slide text", 0, 1.0, "", digest)
        status, reason, ratio = assess_text(text, b"")
    else:
        return _result(relative, file_type, "skip", "none", "unsupported extension", 0, 1.0, "", digest)

    output_relative = ""
    if status in {"clean", "review"}:
        output_relative = _allocate(used, "text", relative)
        _write(output_dir, output_relative, text if text.endswith("\n") else text + "\n")
    elif status == "reject":
        output_relative = _allocate(used, "rejected", relative)
        _write(output_dir, output_relative, f"status: reject\nreason: {reason}\n")
    ratio = noise_ratio(text) if text else ratio
    return _result(relative, file_type, status, action, reason, len(text), ratio, output_relative, digest)


def _manifest_payload(results: list[ExtractionResult]) -> dict[str, object]:
    counts = {status: 0 for status in STATUSES}
    for result in results:
        counts[result.status] += 1
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "counts": counts,
        "results": [result.to_dict() for result in results],
    }
