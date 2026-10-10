from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from locobox_cli.adapters.pdftotext import run_pdftotext_layout
from locobox_cli.adapters.paths import find_repo_root
from locobox_cli.adapters.queue_fs import FilesystemQueueStore
from locobox_cli.adapters.sources.piko.catalog import extract_piko_catalog_rows, rows_to_queue
from locobox_cli.application.ports.queue_store import QueueKind
from locobox_cli.application.queue.parse import render_queue_text
from locobox_cli.domain.manufacturer import Manufacturer

app = typer.Typer(help="Catalog PDF → text → candidate queue.", no_args_is_help=True)


@app.command("pdf-to-text")
def pdf_to_text_cmd(
    pdf: Path = typer.Option(..., "--pdf"),
    out: Path = typer.Option(..., "--out", "-o"),
) -> None:
    """Run pdftotext -layout."""
    run_pdftotext_layout(pdf, out)
    typer.echo(f"wrote {out}")


@app.command("extract")
def extract_cmd(
    source: str = typer.Option("piko", "--source", "-s", help="Manufacturer source adapter"),
    text_file: Path = typer.Option(..., "--text-file", "-t"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Candidate queue path"),
    campaign: Optional[str] = typer.Option(None, "--campaign"),
    min_price_eur: Optional[float] = typer.Option(None, "--min-price-eur"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Extract article candidates from catalog text (PIKO)."""
    mfr = Manufacturer.parse(source)
    if mfr != Manufacturer.PIKO:
        raise typer.BadParameter("only --source piko is implemented so far")
    text = text_file.read_text(encoding="utf-8", errors="replace")
    rows = extract_piko_catalog_rows(text)
    queue = rows_to_queue(rows, min_price_eur=min_price_eur)
    rendered = render_queue_text(queue, numbers_only=False)

    root = repo_root or find_repo_root()
    target = out
    if campaign:
        store = FilesystemQueueStore(root)
        path = store.save(campaign, QueueKind.CANDIDATES, queue)
        target = path
    elif out is None:
        typer.echo(rendered, nl=False)
        typer.echo(
            json.dumps({"ok": True, "count": len(queue.entries), "source": mfr.slug}),
            err=True,
        )
        return
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        target = out

    typer.echo(
        json.dumps(
            {"ok": True, "count": len(queue.entries), "source": mfr.slug, "out": str(target)},
            ensure_ascii=False,
        )
    )
