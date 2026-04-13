import typer
from . import commands

app = typer.Typer(help="Local-first markdown wiki CLI.")


@app.command()
def init(
    library: str | None = typer.Option(None, "--library", "-C", help="Library root path."),
) -> None:
    """Initialize library folders and starter files."""
    commands.cmd_init(library=library)


@app.command("list")
def list_notes(
    library: str | None = typer.Option(None, "--library", "-C"),
    note_type: str | None = typer.Option(None, "--type"),
    tag: str | None = typer.Option(None, "--tag"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List notes from wiki."""
    commands.cmd_list(library=library, note_type=note_type, tag=tag, as_json=as_json)


@app.command()
def ingest(
    input: str = typer.Argument(..., help="Input file or directory."),
    library: str | None = typer.Option(None, "--library", "-C"),
    note_type: str = typer.Option("source", "--type"),
    title: str | None = typer.Option(None, "--title"),
    note_id: str | None = typer.Option(None, "--id"),
) -> None:
    """Ingest local files into raw and create notes."""
    commands.cmd_ingest(input_path=input, library=library, note_type=note_type, title=title, note_id=note_id)


@app.command()
def search(
    query: str = typer.Argument(...),
    library: str | None = typer.Option(None, "--library", "-C"),
    limit: int = typer.Option(10, "--limit"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Keyword search in notes."""
    commands.cmd_search(query=query, library=library, limit=limit, as_json=as_json)


@app.command()
def open(
    id_or_path: str = typer.Argument(...),
    library: str | None = typer.Option(None, "--library", "-C"),
) -> None:
    """Open a note by id or path."""
    commands.cmd_open(id_or_path=id_or_path, library=library)


@app.command()
def summarize(
    id_or_path: str = typer.Argument(...),
    library: str | None = typer.Option(None, "--library", "-C"),
    mode: str = typer.Option("local", "--mode"),
) -> None:
    """Summarize note content (local mode only)."""
    commands.cmd_summarize(id_or_path=id_or_path, library=library, mode=mode)


@app.command()
def link(
    from_id: str = typer.Argument(...),
    to_id: str = typer.Argument(...),
    library: str | None = typer.Option(None, "--library", "-C"),
    relation: str = typer.Option("related", "--relation"),
    bidirectional: bool = typer.Option(True, "--bidirectional/--no-bidirectional"),
) -> None:
    """Create relationship between notes via frontmatter."""
    commands.cmd_link(from_id=from_id, to_id=to_id, library=library, relation=relation, bidirectional=bidirectional)


@app.command()
def check(
    library: str | None = typer.Option(None, "--library", "-C"),
    strict: bool = typer.Option(False, "--strict"),
) -> None:
    """Validate schema and links."""
    commands.cmd_check(library=library, strict=strict)


if __name__ == "__main__":
    app()
