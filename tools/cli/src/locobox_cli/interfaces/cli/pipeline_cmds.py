from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from locobox_cli.adapters.article_fs import FilesystemArticleRepository
from locobox_cli.adapters.paths import find_repo_root
from locobox_cli.adapters.queue_fs import FilesystemQueueStore
from locobox_cli.adapters.rules_yaml import load_rules_tree
from locobox_cli.application.pipeline.run import RunArticlePipeline
from locobox_cli.application.queue.clear import ClearQueueWorkingState

app = typer.Typer(help="Shared article pipeline (YAML rules) and clear.", no_args_is_help=True)


def _default_rules_dir(root: Path) -> Path:
    return root / "rules"


@app.command("apply")
def apply_cmd(
    file: Optional[list[Path]] = typer.Option(None, "--file", "-f", help="Article JSON path(s)"),
    directory: Optional[Path] = typer.Option(None, "--dir", "-d", help="Directory of article JSON"),
    rules: Optional[Path] = typer.Option(None, "--rules", "-r", help="Rules file or directory"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    no_swiss_ss: bool = typer.Option(False, "--no-swiss-ss"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Normalize text and apply YAML fix rules to article JSON."""
    root = repo_root or find_repo_root()
    rules_path = rules or _default_rules_dir(root)
    rule_list = load_rules_tree(rules_path)
    pipeline = RunArticlePipeline(rules=tuple(rule_list), apply_swiss_ss=not no_swiss_ss)
    repo = FilesystemArticleRepository(root)

    paths: list[Path] = []
    if file:
        paths.extend(file)
    if directory:
        paths.extend(sorted(directory.glob("*.json")))
    if not paths:
        raise typer.BadParameter("provide --file and/or --dir")

    reports: list[dict] = []
    for path in paths:
        original = repo.load_path(path)
        result = pipeline.run(original)
        reports.append(
            {
                "file": str(path),
                "changed": result.changed,
                "swiss_ss_changes": result.swiss_ss_changes,
                "rules": [
                    {
                        "id": h.rule_id,
                        "field": h.field,
                        "before": h.before,
                        "after": h.after,
                    }
                    for h in result.rule_hits
                ],
                "dry_run": dry_run,
            }
        )
        if result.changed and not dry_run:
            repo.save_path(path, result.article)

    typer.echo(
        json.dumps(
            {
                "ok": True,
                "rules_loaded": len(rule_list),
                "files": len(reports),
                "changed_files": sum(1 for r in reports if r["changed"]),
                "results": reports,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("clear")
def clear_cmd(
    campaign: str = typer.Option(..., "--campaign"),
    candidates: bool = typer.Option(True, "--candidates/--no-candidates"),
    approved: bool = typer.Option(True, "--approved/--no-approved"),
    html_cache: bool = typer.Option(False, "--html-cache"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Clear campaign working state (same as queue clear)."""
    if not dry_run and not yes:
        typer.confirm(f"Clear working state for campaign {campaign!r}?", abort=True)
    root = repo_root or find_repo_root()
    removed = ClearQueueWorkingState(FilesystemQueueStore(root)).run(
        campaign,
        candidates=candidates,
        approved=approved,
        html_cache=html_cache,
        dry_run=dry_run,
    )
    prefix = "would remove" if dry_run else "removed"
    if not removed:
        typer.echo("nothing to clear")
        return
    for path in removed:
        typer.echo(f"{prefix}: {path}")
