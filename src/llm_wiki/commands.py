from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

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


def cmd_ingest(input_path: str, library: str | None = None, note_type: str = "source", title: str | None = None, note_id: str | None = None) -> None:
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
        body = f"# {fm['title']}\n\nSource: `{dst.relative_to(root)}`\n"
        if extracted.strip():
            body += "\n## Extract\n\n```\n" + extracted.strip() + "\n```\n"
        write_note(Note(path=note_path, fm=fm, body=body))
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


def cmd_summarize(id_or_path: str, library: str | None = None, mode: str = "local") -> None:
    root = library_root(library)
    note = resolve_note(root, id_or_path)
    if not note:
        fail("Target not found.", EXIT_NOT_FOUND)
    if mode != "local":
        fail("Only local mode is currently implemented.", EXIT_ARGS)
    lines = [l.strip() for l in note.body.splitlines() if l.strip()]
    heading = lines[0] if lines else note.fm.get("title", "Untitled")
    paras = [l for l in lines[1:] if not l.startswith("#")]
    summary = " ".join(paras[:3])[:500]
    typer.echo(f"Summary for {note.fm.get('id', note.path.stem)}")
    typer.echo(f"- Heading: {heading}")
    typer.echo(f"- Summary: {summary or 'No content.'}")


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
    if errors:
        typer.echo("Check failed:")
        for e in errors:
            typer.echo(f"- {e}")
        raise typer.Exit(EXIT_VALIDATION)
    typer.echo(f"Check passed ({len(notes)} notes).")
