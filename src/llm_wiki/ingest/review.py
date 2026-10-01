"""Human review queue for extracts that are not canonical yet."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..core import (
    EXIT_NOT_FOUND,
    EXIT_VALIDATION,
    WIKI_DIR,
    Note,
    append_log,
    ensure_structure,
    now_iso,
    slugify,
    write_note,
)
from .quality import assess_text


class ReviewFailure(Exception):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    source_relative: str
    file_type: str
    text_chars: int
    created_at: str
    sha256: str
    output_relative_path: str
    status: str
    ocr_used: bool
    ocr_provider: str
    ocr_pages: int


def pending_review_items(root: Path) -> list[ReviewItem]:
    decisions = _decisions(root)
    return [item for item in _load_items(root) if decisions.get(item.review_id) is None]


def show_review_item(root: Path, review_id: str) -> tuple[ReviewItem, str]:
    item = _find(root, review_id)
    _verify_source(root, item)
    return item, _read_text(root, item)


def approve_review_item(root: Path, review_id: str) -> tuple[str, str]:
    """Return ``(note_id, outcome)`` where outcome is ``created`` or ``already``."""
    item = _find(root, review_id)
    decision = _decisions(root).get(item.review_id)
    if decision == "approved":
        return "", "already"
    if decision == "rejected":
        raise ReviewFailure(f"Cannot approve {item.review_id}: already rejected.", EXIT_VALIDATION)
    _verify_source(root, item)
    text = _read_text(root, item)
    status, reason, _ratio = assess_text(text, b"")
    if status == "reject":
        raise ReviewFailure(f"Reviewed text failed the quality gate: {reason}", EXIT_VALIDATION)
    note_id = _write_note(root, item, text)
    _append_decision(root, item, "approved", note_id)
    return note_id, "created"


def reject_review_item(root: Path, review_id: str) -> str:
    """Return ``created`` or ``already``."""
    item = _find(root, review_id)
    decision = _decisions(root).get(item.review_id)
    if decision == "rejected":
        return "already"
    if decision == "approved":
        raise ReviewFailure(f"Cannot reject {item.review_id}: already approved.", EXIT_VALIDATION)
    _verify_source(root, item)
    _append_decision(root, item, "rejected", None)
    return "created"


def _manifest_path(root: Path) -> Path:
    return root / "derived" / "extraction" / "manifests" / "extraction.json"


def _log_path(root: Path) -> Path:
    return root / "derived" / "extraction" / "manifests" / "review.jsonl"


def _load_items(root: Path) -> list[ReviewItem]:
    path = _manifest_path(root)
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION)
    created_at = str(payload.get("created_at") or "-")
    items: list[ReviewItem] = []
    for entry in payload["results"]:
        if not isinstance(entry, dict):
            raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION)
        if entry.get("status") != "review":
            continue
        items.append(_item_from(entry, created_at))
    return items


def _item_from(entry: dict, created_at: str) -> ReviewItem:
    relative = _portable(str(entry.get("relative_path") or ""))
    output_relative = _portable(str(entry.get("output_relative_path") or ""))
    digest = str(entry.get("sha256") or "")
    if not relative or not output_relative or not _is_sha256(digest):
        raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION)
    return ReviewItem(
        review_id=review_id_for(relative, digest),
        source_relative=relative,
        file_type=str(entry.get("file_type") or "unknown"),
        text_chars=int(entry.get("text_chars") or 0),
        created_at=created_at,
        sha256=digest,
        output_relative_path=output_relative,
        status="review",
        ocr_used=bool(entry.get("ocr_used")),
        ocr_provider=str(entry.get("ocr_provider") or ""),
        ocr_pages=int(entry.get("ocr_pages") or 0),
    )


def review_id_for(relative: str, digest: str) -> str:
    stem = slugify(Path(relative).stem) or "item"
    suffix = hashlib.sha256(f"{relative}\n{digest}".encode("utf-8")).hexdigest()[:12]
    return f"{stem}-{suffix}"


def _portable(value: str) -> str:
    text = value.replace("\\", "/")
    path = Path(text)
    if not text or path.is_absolute() or text.startswith("/") or ".." in path.parts or ":" in text:
        return ""
    return path.as_posix()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _find(root: Path, review_id: str) -> ReviewItem:
    matches = [item for item in _load_items(root) if item.review_id == review_id]
    if not matches:
        raise ReviewFailure("Review item not found.", EXIT_NOT_FOUND)
    if len(matches) > 1:
        raise ReviewFailure("Review id is ambiguous.", EXIT_VALIDATION)
    return matches[0]


def _decisions(root: Path) -> dict[str, str]:
    path = _log_path(root)
    if not path.is_file():
        return {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION) from exc
    latest: dict[str, str] = {}
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION) from exc
        if not isinstance(event, dict):
            raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION)
        review_id = str(event.get("review_id") or "")
        decision = str(event.get("decision") or "")
        if not review_id or decision not in {"approved", "rejected"}:
            raise ReviewFailure("Review metadata is unreadable.", EXIT_VALIDATION)
        latest[review_id] = decision
    return latest


def _verify_source(root: Path, item: ReviewItem) -> None:
    path = _inside(root / "raw", item.source_relative)
    if not path.is_file():
        raise ReviewFailure("Review metadata does not match the stored source.", EXIT_VALIDATION)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != item.sha256:
        raise ReviewFailure("Review metadata does not match the stored source.", EXIT_VALIDATION)


def _read_text(root: Path, item: ReviewItem) -> str:
    path = _inside(root / "derived" / "extraction", item.output_relative_path)
    if not path.is_file():
        raise ReviewFailure("Reviewed text is missing.", EXIT_VALIDATION)
    return path.read_text(encoding="utf-8")


def _inside(base: Path, relative: str) -> Path:
    root = base.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise ReviewFailure("Review metadata is not portable.", EXIT_VALIDATION)
    return target


def _append_decision(root: Path, item: ReviewItem, decision: str, note_id: str | None) -> None:
    path = _log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": 1,
        "event": "review",
        "review_id": item.review_id,
        "source_relative": item.source_relative,
        "source_sha256": item.sha256,
        "decision": decision,
        "note_id": note_id,
        "timestamp": now_iso(),
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _write_note(root: Path, item: ReviewItem, text: str) -> str:
    from ..commands import _summarize_text, _update_index

    ensure_structure(root)
    stem = Path(item.source_relative).stem
    base = slugify(stem) or "untitled"
    candidate_id = base
    index = 2
    while (root / WIKI_DIR / f"{candidate_id}.md").exists():
        candidate_id = f"{base}-{index}"
        index += 1
    raw_relative = f"raw/{item.source_relative}"
    title = stem.replace("_", " ").title()
    summary = _summarize_text(title, text)
    timestamp = now_iso()
    frontmatter: dict[str, object] = {
        "id": candidate_id,
        "title": title,
        "type": "source",
        "created": timestamp,
        "updated": timestamp,
        "sources": [{"ref": raw_relative, "kind": "file", "ingested_at": timestamp}],
        "related": [],
        "source_file": raw_relative,
        "source_sha256": item.sha256,
        "extraction_status": "reviewed",
    }
    if item.ocr_used:
        frontmatter["ocr_used"] = True
        frontmatter["ocr_provider"] = item.ocr_provider
        frontmatter["ocr_pages"] = item.ocr_pages
    body = f"# {title}\n\n## Summary\n\n{summary}\n\n## Source\n\n- `{raw_relative}`\n\n{text.strip()}\n"
    write_note(Note(path=root / WIKI_DIR / f"{candidate_id}.md", fm=frontmatter, body=body))
    _update_index(root, candidate_id, title, summary or "Reviewed source note.")
    append_log(root, "review", f"{item.source_relative} -> {candidate_id}")
    return candidate_id
