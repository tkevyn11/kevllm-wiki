from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any
import re

import typer
import yaml

from .core import (
    DOCS_DIR,
    EXIT_ARGS,
    EXIT_NOT_FOUND,
    EXIT_VALIDATION,
    LINK_PATTERN,
    MANIFEST_FILE,
    RAW_DIR,
    REQ_FIELDS,
    WIKI_DIR,
    WORK_DIR,
    Note,
    append_log,
    ensure_structure,
    fail,
    library_root,
    maybe_read_text,
    now_iso,
    read_note,
    resolve_note,
    slugify,
    wiki_files,
    write_note,
)


def cmd_init(library: str | None = None) -> None:
    root = library_root(library)
    ensure_structure(root)
    typer.echo(f"Initialized library at {root}")


def cmd_list(library: str | None = None, note_type: str | None = None, tag: str | None = None, as_json: bool = False) -> None:
    root = library_root(library)
    items: list[dict[str, str]] = []
    for path in wiki_files(root):
        note = read_note(path)
        if note_type and note.fm.get("type") != note_type:
            continue
        tags = note.fm.get("tags", []) or []
        if tag and tag not in tags:
            continue
        items.append(
            {
                "id": str(note.fm.get("id", "")),
                "title": str(note.fm.get("title", path.stem)),
                "type": str(note.fm.get("type", "")),
                "updated": str(note.fm.get("updated", "")),
                "path": str(path.relative_to(root)),
            }
        )
    if as_json:
        typer.echo(json.dumps(items, indent=2))
        return
    if not items:
        typer.echo("No notes found.")
        return
    for it in items:
        typer.echo(f"{it['id']:24} {it['type']:12} {it['updated']:24} {it['title']}")


def cmd_ingest(
    input_path: str,
    library: str | None = None,
    note_type: str = "source",
    title: str | None = None,
    note_id: str | None = None,
    summarize: bool = True,
    link_suggestions: bool = False,
    touch_related: bool = False,
) -> None:
    root = library_root(library)
    ensure_structure(root)
    src = Path(input_path).resolve()
    if not src.exists():
        fail("Input not found.", EXIT_ARGS)
    files = [p for p in src.rglob("*") if p.is_file()] if src.is_dir() else [src]
    created = 0
    for file_path in files:
        rel = file_path.name
        dst = root / RAW_DIR / rel
        if dst.exists():
            stem = dst.stem
            i = 2
            while True:
                candidate = dst.with_name(f"{stem}-{i}{dst.suffix}")
                if not candidate.exists():
                    dst = candidate
                    break
                i += 1
        shutil.copy2(file_path, dst)
        base = note_id or slugify(file_path.stem)
        candidate_id = base
        i = 2
        while (root / WIKI_DIR / f"{candidate_id}.md").exists():
            candidate_id = f"{base}-{i}"
            i += 1
        note_path = root / WIKI_DIR / f"{candidate_id}.md"
        ts = now_iso()
        fm = {
            "id": candidate_id,
            "title": title or file_path.stem.replace("_", " ").title(),
            "type": note_type,
            "created": ts,
            "updated": ts,
            "sources": [{"ref": str(dst.relative_to(root)), "kind": "file", "ingested_at": ts}],
            "related": [],
        }
        extracted = maybe_read_text(file_path)
        summary = _summarize_text(fm["title"], extracted) if summarize else ""
        body = f"# {fm['title']}\n\n"
        if summarize:
            body += f"## Summary\n\n{summary}\n\n"
        body += f"## Source\n\n- `{dst.relative_to(root)}`\n"
        if extracted.strip():
            body += "\n## Extract\n\n```\n" + extracted.strip() + "\n```\n"
        write_note(Note(path=note_path, fm=fm, body=body))
        _update_index(root, candidate_id, fm["title"], summary or "Ingested source note.")
        if link_suggestions:
            linked_ids = _auto_link_suggestions(root, candidate_id, fm["title"], extracted)
            if linked_ids:
                append_log(root, "link-suggest", f"{candidate_id} -> {', '.join(linked_ids)}")
                if touch_related:
                    touched = _touch_related_notes(root, linked_ids)
                    if touched:
                        append_log(root, "touch-related", f"{candidate_id} refreshed {', '.join(touched)}")
        with (root / WORK_DIR / MANIFEST_FILE).open("a", encoding="utf-8") as mf:
            mf.write(
                json.dumps(
                    {
                        "event": "ingest",
                        "ingested_at": ts,
                        "input": str(file_path),
                        "status": "success",
                        "note_id": candidate_id,
                    }
                )
                + "\n"
            )
        append_log(root, "ingest", f"{file_path.name} -> {candidate_id}")
        created += 1
    typer.echo(f"Ingested {created} file(s).")


def cmd_search(query: str, library: str | None = None, limit: int = 10, as_json: bool = False) -> None:
    root = library_root(library)
    q = query.lower()
    results: list[dict[str, Any]] = []
    for wf in wiki_files(root):
        n = read_note(wf)
        title = str(n.fm.get("title", ""))
        blob = f"{title}\n{yaml.safe_dump(n.fm)}\n{n.body}".lower()
        if q not in blob:
            continue
        score = 0
        score += 5 if q in title.lower() else 0
        score += blob.count(q)
        idx = blob.find(q)
        snippet = n.body[max(0, idx - 40) : idx + 120].replace("\n", " ").strip() if idx >= 0 else ""
        results.append(
            {
                "id": n.fm.get("id", wf.stem),
                "title": title or wf.stem,
                "path": str(wf.relative_to(root)),
                "score": score,
                "snippet": snippet,
            }
        )
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]
    if as_json:
        typer.echo(json.dumps(results, indent=2))
        return
    if not results:
        typer.echo("No matches.")
        return
    for r in results:
        typer.echo(f"[{r['score']:>3}] {r['id']}  {r['path']}\n  {r['snippet']}")


def cmd_open(id_or_path: str, library: str | None = None) -> None:
    root = library_root(library)
    note = resolve_note(root, id_or_path)
    if not note:
        fail("Target not found.", EXIT_NOT_FOUND)
    p = note.path
    if sys.platform.startswith("win"):
        os.startfile(str(p))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(p)], check=False)
    else:
        try:
            subprocess.run(["xdg-open", str(p)], check=False)
        except FileNotFoundError:
            webbrowser.open(p.as_uri())
    typer.echo(f"Opened {p}")


def cmd_summarize(id_or_path: str, library: str | None = None, mode: str = "local", write: bool = False) -> None:
    root = library_root(library)
    note = resolve_note(root, id_or_path)
    if not note:
        fail("Target not found.", EXIT_NOT_FOUND)
    if mode != "local":
        fail("Only local mode is currently implemented.", EXIT_ARGS)
    lines = [l.strip() for l in note.body.splitlines() if l.strip()]
    heading = lines[0] if lines else note.fm.get("title", "Untitled")
    paras = [l for l in lines[1:] if not l.startswith("#")]
    text_for_summary = " ".join(paras).strip()
    if not text_for_summary or text_for_summary.lower().startswith("source:"):
        text_for_summary = _read_sources_text(root, note)
    summary = _summarize_text(str(note.fm.get("title", "Untitled")), text_for_summary)
    typer.echo(f"Summary for {note.fm.get('id', note.path.stem)}")
    typer.echo(f"- Heading: {heading}")
    typer.echo(f"- Summary: {summary or 'No content.'}")
    if write:
        note.body = _upsert_summary_section(note.body, summary)
        note.fm["updated"] = now_iso()
        write_note(note)
        _update_index(root, str(note.fm.get("id", note.path.stem)), str(note.fm.get("title", note.path.stem)), summary)
        append_log(root, "summarize", f"{note.fm.get('id', note.path.stem)} updated summary")
        typer.echo(f"Updated note summary: {note.path.relative_to(root)}")


def cmd_query(question: str, library: str | None = None, top_k: int = 5, save: bool = False) -> None:
    root = library_root(library)
    q_terms = [t for t in re.findall(r"[a-z0-9]+", question.lower()) if len(t) > 2]
    if not q_terms:
        fail("Query must contain searchable terms.", EXIT_ARGS)
    scored: list[tuple[int, Note]] = []
    for wf in wiki_files(root):
        note = read_note(wf)
        if str(note.fm.get("type", "")).lower() == "query":
            continue
        hay = f"{note.fm.get('title', '')}\n{yaml.safe_dump(note.fm)}\n{note.body}".lower()
        score = sum(hay.count(term) for term in q_terms)
        if score > 0:
            scored.append((score, note))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]
    if not top:
        typer.echo("No relevant notes found.")
        return
    snippets: list[str] = []
    citations: list[str] = []
    for _, note in top:
        summ = _extract_summary_section(note.body) or _summarize_text(str(note.fm.get("title", "")), note.body)
        snippets.append(f"- **{note.fm.get('title', note.path.stem)}**: {summ}")
        citations.append(f"- [{note.fm.get('id', note.path.stem)}]({note.path.relative_to(root)})")
    typer.echo(f"# Query\n\nQuestion: {question}\n")
    typer.echo("## Answer\n")
    typer.echo("\n".join(snippets))
    typer.echo("\n\n## Sources\n")
    typer.echo("\n".join(citations))
    if save:
        qid = f"query-{slugify(question)[:40]}"
        path = root / WIKI_DIR / f"{qid}.md"
        ts = now_iso()
        fm = {
            "id": qid,
            "title": f"Query: {question}",
            "type": "query",
            "created": ts,
            "updated": ts,
            "sources": [{"ref": str(n.path.relative_to(root)), "kind": "file", "ingested_at": ts} for _, n in top],
            "related": [str(n.fm.get("id", n.path.stem)) for _, n in top],
        }
        body = f"# Query: {question}\n\n## Answer\n\n" + "\n".join(snippets) + "\n\n## Sources\n\n" + "\n".join(citations) + "\n"
        write_note(Note(path=path, fm=fm, body=body))
        _update_index(root, qid, fm["title"], f"Synthesized answer from {len(top)} notes.")
        append_log(root, "query", f"{question} -> {qid}")
        typer.echo(f"\nSaved query note: {path.relative_to(root)}")


def cmd_link(from_id: str, to_id: str, library: str | None = None, relation: str = "related", bidirectional: bool = True) -> None:
    root = library_root(library)
    from_note = resolve_note(root, from_id)
    to_note = resolve_note(root, to_id)
    if not from_note or not to_note:
        fail("One or both notes not found.", EXIT_NOT_FOUND)
    for a, b in [(from_note, to_note), (to_note, from_note)]:
        if a is to_note and not bidirectional:
            continue
        rel = a.fm.get(relation, []) or []
        target_id = b.fm.get("id", b.path.stem)
        if target_id not in rel:
            rel.append(target_id)
        a.fm[relation] = rel
        a.fm["updated"] = now_iso()
        write_note(a)
    append_log(root, "link", f"{from_note.fm.get('id')} <-> {to_note.fm.get('id')}")
    typer.echo(f"Linked {from_note.fm.get('id')} and {to_note.fm.get('id')}.")


def cmd_check(library: str | None = None, strict: bool = False) -> None:
    root = library_root(library)
    notes = [read_note(p) for p in wiki_files(root)]
    errors = _collect_structural_errors(root, notes, strict=strict)
    if errors:
        typer.echo("Check failed:")
        for e in errors:
            typer.echo(f"- {e}")
        raise typer.Exit(EXIT_VALIDATION)
    typer.echo(f"Check passed ({len(notes)} notes).")


def cmd_lint(library: str | None = None, strict: bool = False) -> None:
    root = library_root(library)
    notes = [read_note(p) for p in wiki_files(root)]
    errors = _collect_structural_errors(root, notes, strict=strict)
    id_to_note = {str(n.fm.get("id", n.path.stem)): n for n in notes}
    inbound: dict[str, int] = {nid: 0 for nid in id_to_note}
    for n in notes:
        for rid in n.fm.get("related", []) or []:
            r = str(rid)
            if r in inbound:
                inbound[r] += 1
    warnings: list[str] = []
    for nid, cnt in inbound.items():
        if cnt == 0:
            warnings.append(f"orphan note (no inbound related links): {nid}")
    for n in notes:
        if "## Summary" not in n.body:
            warnings.append(f"missing summary section: {n.path.name}")
    if errors:
        typer.echo("Lint structural issues:")
        for e in errors:
            typer.echo(f"- {e}")
        raise typer.Exit(EXIT_VALIDATION)
    typer.echo(f"Lint passed structural checks ({len(notes)} notes).")
    if warnings:
        typer.echo("Lint warnings:")
        for w in warnings:
            typer.echo(f"- {w}")
    else:
        typer.echo("No lint warnings.")


def _collect_structural_errors(root: Path, notes: list[Note], strict: bool) -> list[str]:
    errors: list[str] = []
    id_to_path: dict[str, Path] = {}
    for n in notes:
        missing = sorted(list(REQ_FIELDS - set(n.fm.keys())))
        if missing:
            errors.append(f"{n.path.name}: missing fields {missing}")
        nid = str(n.fm.get("id", ""))
        if nid:
            if nid in id_to_path:
                errors.append(f"duplicate id: {nid} in {n.path.name} and {id_to_path[nid].name}")
            id_to_path[nid] = n.path
    for n in notes:
        related = n.fm.get("related", []) or []
        for rid in related:
            if str(rid) not in id_to_path:
                errors.append(f"{n.path.name}: related id not found -> {rid}")
        for m in LINK_PATTERN.finditer(n.body):
            target = m.group(1).split("#")[0]
            if target.startswith(("http://", "https://", "mailto:")) or target == "":
                continue
            rel_path = (n.path.parent / target).resolve()
            root_path = (root / target).resolve()
            if not rel_path.exists() and not root_path.exists():
                errors.append(f"{n.path.name}: broken link -> {target}")
    if strict:
        for n in notes:
            if not isinstance(n.fm.get("sources"), list):
                errors.append(f"{n.path.name}: sources must be a list")
    return errors


def _summarize_text(title: str, text: str, max_sentences: int = 3) -> str:
    content = " ".join((text or "").split())
    if not content:
        return f"No extractable text yet for {title}. Add notes manually or preprocess the source into text."
    sentences = re.split(r"(?<=[.!?])\s+", content)
    picked = [s.strip() for s in sentences if s.strip()][:max_sentences]
    summary = " ".join(picked).strip()
    return summary[:700]


def _extract_summary_section(body: str) -> str:
    if "## Summary" not in body:
        return ""
    tail = body.split("## Summary", 1)[1]
    if "\n## " in tail:
        tail = tail.split("\n## ", 1)[0]
    return " ".join(line.strip() for line in tail.splitlines() if line.strip()).strip()


def _upsert_summary_section(body: str, summary: str) -> str:
    if "## Summary" not in body:
        return body.strip() + f"\n\n## Summary\n\n{summary}\n"
    before, tail = body.split("## Summary", 1)
    after = ""
    if "\n## " in tail:
        _, rest = tail.split("\n## ", 1)
        after = "## " + rest
    rebuilt = before.rstrip() + f"\n\n## Summary\n\n{summary}\n\n"
    if after:
        rebuilt += after.lstrip()
    return rebuilt.rstrip() + "\n"


def _sanitize_index_line_field(s: str) -> str:
    """One-line safe text for index entries (no newlines, no NUL)."""
    t = (s or "").replace("\x00", "")
    t = re.sub(r"[\n\r\x0b\x0c\u0085\u2028\u2029]+", " ", t)
    return " ".join(t.split()).strip()


def _update_index(root: Path, note_id: str, title: str, summary: str) -> None:
    index_path = root / WIKI_DIR / "index.md"
    if not index_path.exists():
        index_path.write_text("# Index\n\n", encoding="utf-8", newline="\n")
    stitle = _sanitize_index_line_field(str(title or "")) or str(note_id)
    ssum = _sanitize_index_line_field(str(summary or ""))[:180]
    line = f"- [{stitle}]({note_id}.md) - {ssum}\n"
    existing = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
    filtered = [ln for ln in existing if f"]({note_id}.md)" not in ln]
    if not filtered:
        filtered = ["# Index\n", "\n"]
    if not any(ln.strip() == "# Index" for ln in filtered):
        filtered.insert(0, "# Index\n")
    if filtered and filtered[-1].strip() != "":
        filtered.append("\n")
    filtered.append(line)
    data = "".join(filtered)
    tmp = index_path.with_name(index_path.name + ".tmp")
    try:
        tmp.write_text(data, encoding="utf-8", newline="\n")
        tmp.replace(index_path)
    except OSError:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def _read_sources_text(root: Path, note: Note) -> str:
    sources = note.fm.get("sources", []) or []
    chunks: list[str] = []
    for src in sources:
        if not isinstance(src, dict):
            continue
        ref = src.get("ref")
        if not isinstance(ref, str) or not ref:
            continue
        path = (root / ref).resolve()
        if not path.exists():
            continue
        extracted = maybe_read_text(path)
        if extracted.strip():
            chunks.append(extracted.strip())
    return "\n".join(chunks)[:6000]


def _auto_link_suggestions(root: Path, note_id: str, title: str, extracted: str) -> list[str]:
    current = resolve_note(root, note_id)
    if not current:
        return []
    current_terms = set(_keyword_terms(f"{title} {extracted}"))
    if not current_terms:
        return []
    candidates: list[tuple[int, Note]] = []
    for wf in wiki_files(root):
        n = read_note(wf)
        nid = str(n.fm.get("id", wf.stem))
        if nid == note_id:
            continue
        terms = set(_keyword_terms(f"{n.fm.get('title', '')} {n.body}"))
        overlap = len(current_terms & terms)
        if overlap >= 2:
            candidates.append((overlap, n))
    candidates.sort(key=lambda x: x[0], reverse=True)
    linked: list[str] = []
    for _, n in candidates[:3]:
        tid = str(n.fm.get("id", n.path.stem))
        if tid in (current.fm.get("related", []) or []):
            continue
        current.fm["related"] = (current.fm.get("related", []) or []) + [tid]
        other_rel = n.fm.get("related", []) or []
        if str(current.fm.get("id", note_id)) not in other_rel:
            other_rel.append(str(current.fm.get("id", note_id)))
            n.fm["related"] = other_rel
            n.fm["updated"] = now_iso()
            write_note(n)
        linked.append(tid)
    if linked:
        current.fm["updated"] = now_iso()
        write_note(current)
    return linked


def _keyword_terms(text: str) -> list[str]:
    stop = {"the", "and", "with", "from", "that", "this", "were", "have", "has", "for", "into", "note", "source", "case"}
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) >= 4 and t not in stop]


def _touch_related_notes(root: Path, related_ids: list[str]) -> list[str]:
    refreshed: list[str] = []
    for rid in related_ids:
        note = resolve_note(root, rid)
        if not note:
            continue
        text_for_summary = _read_sources_text(root, note) or note.body
        summary = _summarize_text(str(note.fm.get("title", note.path.stem)), text_for_summary)
        note.body = _upsert_summary_section(note.body, summary)
        note.fm["updated"] = now_iso()
        write_note(note)
        _update_index(root, str(note.fm.get("id", note.path.stem)), str(note.fm.get("title", note.path.stem)), summary)
        refreshed.append(str(note.fm.get("id", note.path.stem)))
    return refreshed
