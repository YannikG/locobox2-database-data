from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from locobox_cli.adapters.paths import find_repo_root
from locobox_cli.application.tags.taxonomy import TagTaxonomy

app = typer.Typer(help="Taxonomy tags under config/tags/.", no_args_is_help=True)


@app.command("ensure")
def ensure_cmd(
    slug: str = typer.Option(..., "--slug", "-s", help="Tag slug (kebab-case)"),
    name: Optional[str] = typer.Option(None, "--name", "-n"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    kind: Optional[str] = typer.Option(
        None, "--kind", help="Optional campaign kind (e.g. neuheiten)"
    ),
    manufacturer_slug: Optional[str] = typer.Option(
        None, "--manufacturer-slug", help="Manufacturer slug for campaign tiles"
    ),
    year: Optional[int] = typer.Option(None, "--year", help="Campaign calendar year"),
    order: Optional[int] = typer.Option(
        None, "--order", help="Order within the same year (higher = later)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Create config/tags/{slug}.json if missing (no overwrite)."""
    root = repo_root or find_repo_root()
    try:
        result = TagTaxonomy(root).ensure(
            slug,
            name=name,
            description=description,
            kind=kind,
            manufacturer_slug=manufacturer_slug,
            year=year,
            order=order,
            dry_run=dry_run,
        )
    except ValueError as exc:
        typer.echo(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
