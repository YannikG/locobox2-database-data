from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from locobox_cli.adapters.article_fs import FilesystemArticleRepository
from locobox_cli.adapters.paths import find_repo_root
from locobox_cli.adapters.queue_fs import FilesystemQueueStore
from locobox_cli.application.ports.queue_store import QueueKind
from locobox_cli.application.queue.approve import ApproveQueue
from locobox_cli.application.queue.clear import ClearQueueWorkingState
from locobox_cli.application.queue.diff import DiffQueueAgainstRepo
from locobox_cli.application.queue.normalize import NormalizeQueue
from locobox_cli.application.queue.parse import parse_queue_text, render_queue_text
from locobox_cli.application.queue.show import format_queue_show
from locobox_cli.domain.manufacturer import Manufacturer

app = typer.Typer(help="Article queue: normalize, diff, show, approve, clear.", no_args_is_help=True)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _parse_id_set(values: Optional[list[str]]) -> Optional[set[str]]:
    if not values:
        return None
    out: set[str] = set()
    for v in values:
        for part in v.split(","):
            part = part.strip()
            if part:
                out.add(part)
    return out or None


@app.command("normalize")
def normalize_cmd(
    articles: Path = typer.Option(..., "--articles", "-a", help="Input queue .txt"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output path (default: stdout)"),
    numbers_only: bool = typer.Option(True, "--numbers-only/--keep-meta"),
) -> None:
    """Deduplicate and canonicalize a queue file."""
    doc, rendered = NormalizeQueue(numbers_only=numbers_only).run(_read_text(articles))
    if out is None:
        typer.echo(rendered, nl=False)
    else:
        _write_text(out, rendered)
        typer.echo(f"wrote {len(doc.entries)} articles -> {out}")


@app.command("diff")
def diff_cmd(
    manufacturer: str = typer.Option(..., "--mfr", "-m", help="Manufacturer slug (piko|roco)"),
    articles: Path = typer.Option(..., "--articles", "-a", help="Queue .txt"),
    out_missing: Optional[Path] = typer.Option(None, "--out-missing", help="Write missing numbers"),
    out_existing: Optional[Path] = typer.Option(None, "--out-existing", help="Write existing numbers"),
    campaign: Optional[str] = typer.Option(
        None,
        "--campaign",
        help="If set, also write diff files under .tmp/import/{campaign}/",
    ),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Compare queue against articles/{mfr}/."""
    root = repo_root or find_repo_root()
    mfr = Manufacturer.parse(manufacturer)
    queue = parse_queue_text(_read_text(articles))
    diff = DiffQueueAgainstRepo(FilesystemArticleRepository(root)).run(mfr, queue)

    payload = {
        "manufacturer": mfr.slug,
        "queue_size": diff.queue_size,
        "repo_size": diff.repo_size,
        "missing": list(diff.missing),
        "existing": list(diff.existing),
        "missing_count": len(diff.missing),
        "existing_count": len(diff.existing),
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))

    missing_text = "\n".join(diff.missing) + ("\n" if diff.missing else "")
    existing_text = "\n".join(diff.existing) + ("\n" if diff.existing else "")

    if out_missing:
        _write_text(out_missing, missing_text)
    if out_existing:
        _write_text(out_existing, existing_text)

    if campaign:
        store = FilesystemQueueStore(root)
        camp = store.campaign_dir(campaign)
        camp.mkdir(parents=True, exist_ok=True)
        _write_text(camp / "diff-missing.txt", missing_text)
        _write_text(camp / "diff-existing.txt", existing_text)


@app.command("show")
def show_cmd(
    articles: Path = typer.Option(..., "--articles", "-a"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n"),
) -> None:
    """Human-readable queue summary."""
    doc = parse_queue_text(_read_text(articles))
    typer.echo(format_queue_show(doc, limit=limit), nl=False)


@app.command("approve")
def approve_cmd(
    candidates: Path = typer.Option(..., "--candidates", "-c", help="Candidate queue"),
    out: Path = typer.Option(..., "--out", "-o", help="Approved queue output"),
    manufacturer: Optional[str] = typer.Option(None, "--mfr", "-m"),
    only_missing: bool = typer.Option(False, "--only-missing"),
    min_price_eur: Optional[float] = typer.Option(None, "--min-price-eur"),
    include: Optional[list[str]] = typer.Option(None, "--include", help="SKU or comma-list"),
    exclude: Optional[list[str]] = typer.Option(None, "--exclude", help="SKU or comma-list"),
    campaign: Optional[str] = typer.Option(
        None,
        "--campaign",
        help="Also save as .tmp/import/{campaign}/approved.txt",
    ),
    numbers_only: bool = typer.Option(False, "--numbers-only/--keep-meta"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Filter candidates into an approved import queue (manual gate)."""
    root = repo_root or find_repo_root()
    cand = parse_queue_text(_read_text(candidates))
    mfr = Manufacturer.parse(manufacturer) if manufacturer else None
    repo = FilesystemArticleRepository(root) if only_missing else None
    approved = ApproveQueue(repo=repo).run(
        cand,
        manufacturer=mfr,
        only_missing=only_missing,
        min_price_eur=min_price_eur,
        include=_parse_id_set(include),
        exclude=_parse_id_set(exclude),
    )
    text = render_queue_text(approved, numbers_only=numbers_only)
    _write_text(out, text)
    typer.echo(f"approved {len(approved.entries)} / {len(cand.entries)} -> {out}")

    if campaign:
        store = FilesystemQueueStore(root)
        path = store.save(campaign, QueueKind.APPROVED, approved)
        typer.echo(f"campaign copy -> {path}")


@app.command("clear")
def clear_cmd(
    campaign: str = typer.Option(..., "--campaign", help="Campaign working dir name"),
    candidates: bool = typer.Option(True, "--candidates/--no-candidates"),
    approved: bool = typer.Option(True, "--approved/--no-approved"),
    html_cache: bool = typer.Option(False, "--html-cache"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Clear pipeline working state for a campaign (not articles/ or rules/)."""
    if not dry_run and not yes:
        typer.confirm(
            f"Clear working state for campaign {campaign!r}?",
            abort=True,
        )
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
