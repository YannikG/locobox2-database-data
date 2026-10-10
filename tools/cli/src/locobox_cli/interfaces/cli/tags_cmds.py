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
    dry_run: bool = typer.Option(False, "--dry-run"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Create config/tags/{slug}.json if missing (no overwrite)."""
    root = repo_root or find_repo_root()
    try:
        result = TagTaxonomy(root).ensure(
            slug, name=name, description=description, dry_run=dry_run
        )
    except ValueError as exc:
        typer.echo(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
