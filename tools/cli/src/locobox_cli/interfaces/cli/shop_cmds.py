from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import typer

from locobox_cli.adapters.article_fs import FilesystemArticleRepository
from locobox_cli.adapters.paths import find_repo_root
from locobox_cli.adapters.rules_yaml import load_rules_tree
from locobox_cli.adapters.shop_cloakbrowser import CloakShopFetcher
from locobox_cli.adapters.sources.piko.parse_pdp import parse_piko_pdp
from locobox_cli.adapters.sources.roco.parse_pdp import parse_roco_pdp
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle
from locobox_cli.application.pipeline.run import RunArticlePipeline
from locobox_cli.application.queue.parse import parse_queue_text
from locobox_cli.application.tags.taxonomy import AppendArticleTag, TagTaxonomy
from locobox_cli.domain.delay import DelayPolicy
from locobox_cli.domain.manufacturer import Manufacturer

app = typer.Typer(help="Shop fetch (CloakBrowser) and PDP parse.", no_args_is_help=True)


def _html_dir(root: Path, campaign: Optional[str], source: str) -> Path:
    if campaign:
        return root / ".tmp" / "import" / campaign / "html"
    return root / ".tmp" / f"{source}-pdp"


@app.command("fetch")
def fetch_cmd(
    source: str = typer.Option(..., "--source", "-s", help="piko | roco"),
    articles: Path = typer.Option(..., "--articles", "-a", help="Approved queue .txt"),
    campaign: Optional[str] = typer.Option(None, "--campaign"),
    delay_min: float = typer.Option(2.5, "--delay-min"),
    delay_max: float = typer.Option(6.0, "--delay-max"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--no-skip-existing"),
    humanize: bool = typer.Option(False, "--humanize"),
    headed: bool = typer.Option(False, "--headed"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Fetch PDP HTML for approved article numbers (CloakBrowser)."""
    mfr = Manufacturer.parse(source)
    site = shop_site_for(mfr.slug)
    root = repo_root or find_repo_root()
    queue = parse_queue_text(articles.read_text(encoding="utf-8"))
    nums = [e.article.value for e in queue.entries]
    html_dir = _html_dir(root, campaign, mfr.slug)
    fetcher = CloakShopFetcher(
        site=site,
        html_dir=html_dir,
        delay=DelayPolicy(delay_min, delay_max),
        headless=not headed,
        humanize=humanize,
    )
    summary = fetcher.fetch_many(nums, skip_existing=skip_existing)
    if summary.blocked and campaign:
        blocked = [r.article for r in (summary.results or []) if r.error == "blocked"]
        path = root / ".tmp" / "import" / campaign / "blocked.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(blocked) + ("\n" if blocked else ""), encoding="utf-8")
    payload = {
        "ok": summary.ok,
        "fail": summary.fail,
        "skipped": summary.skipped,
        "blocked": summary.blocked,
        "source": mfr.slug,
        "html_dir": str(html_dir),
        "results": [
            {
                "article": r.article,
                "ok": r.ok,
                "skipped": r.skipped,
                "url": r.url,
                "error": r.error,
                "path": str(r.path) if r.path else None,
            }
            for r in (summary.results or [])
        ],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if summary.blocked or summary.fail:
        raise typer.Exit(code=1)


@app.command("parse")
def parse_cmd(
    source: str = typer.Option(..., "--source", "-s", help="piko | roco"),
    html_dir: Optional[Path] = typer.Option(None, "--html-dir"),
    html_file: Optional[Path] = typer.Option(None, "--html-file"),
    article: Optional[str] = typer.Option(None, "--article"),
    campaign: Optional[str] = typer.Option(None, "--campaign"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Import tag slug (optional)"),
    campaign_tag: Optional[str] = typer.Option(
        None, "--campaign-tag", help="Alias for --tag"
    ),
    append_tag_if_exists: bool = typer.Option(
        False,
        "--append-tag-if-exists",
        help="If article JSON exists: append --tag only (no overwrite)",
    ),
    apply_pipeline: bool = typer.Option(True, "--pipeline/--no-pipeline"),
    write: bool = typer.Option(True, "--write/--no-write"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Parse PDP HTML into article JSON (optional shared pipeline)."""
    mfr = Manufacturer.parse(source)
    site = shop_site_for(mfr.slug)
    root = repo_root or find_repo_root()
    repo = FilesystemArticleRepository(root)
    import_tag = (tag or campaign_tag or "").strip() or None

    if append_tag_if_exists and not import_tag:
        raise typer.BadParameter("--append-tag-if-exists requires --tag")
    if import_tag:
        try:
            import_tag = TagTaxonomy(root).require(import_tag)
        except (ValueError, FileNotFoundError) as exc:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
            raise typer.Exit(code=1) from exc

    files: list[tuple[str, Path]] = []
    if html_file:
        num = article or html_file.stem
        files.append((num, html_file))
    else:
        d = html_dir or _html_dir(root, campaign, mfr.slug)
        for path in sorted(d.glob("*.html")):
            files.append((path.stem, path))
    if not files:
        raise typer.BadParameter("no HTML files found")

    pipeline = None
    if apply_pipeline:
        rules = load_rules_tree(root / "rules")
        pipeline = RunArticlePipeline(rules=tuple(rules))

    validator = ValidateArticle.from_contracts(root)
    reports: list[dict] = []
    fail = 0
    skipped = 0
    appended = 0
    for num, path in files:
        out_path = repo.article_path(mfr, num)
        try:
            if out_path.is_file():
                if append_tag_if_exists and import_tag:
                    data = repo.load_path(out_path)
                    new_data, result = AppendArticleTag(root).run_one(
                        data, import_tag, article_number=num, path=out_path
                    )
                    if result.changed and write and not dry_run:
                        repo.save_path(out_path, new_data)
                    if result.changed:
                        appended += 1
                    else:
                        skipped += 1
                    reports.append(
                        {
                            "article": num,
                            "ok": True,
                            "action": "append_tag" if result.changed else "tag_present",
                            "file": str(out_path),
                            "tags": result.tags,
                            "dry_run": dry_run or not write,
                        }
                    )
                    continue
                skipped += 1
                reports.append(
                    {
                        "article": num,
                        "ok": True,
                        "action": "skipped_existing",
                        "file": str(out_path),
                    }
                )
                continue

            html = path.read_text(encoding="utf-8", errors="replace")
            m = re.search(
                r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
                html,
                re.I,
            )
            if not m:
                m = re.search(
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:url["\']',
                    html,
                    re.I,
                )
            canon = m.group(1) if m else site.fallback_pdp_url(num)
            if mfr == Manufacturer.PIKO:
                raw = parse_piko_pdp(
                    html, canonical_url=canon, article=num, campaign_tag=import_tag
                )
            else:
                raw = parse_roco_pdp(
                    html, canonical_url=canon, article=num, campaign_tag=import_tag
                )
            if pipeline:
                raw = pipeline.run(raw).article
            validator.assert_valid(raw)
            reports.append(
                {
                    "article": num,
                    "ok": True,
                    "action": "created",
                    "file": str(out_path),
                    "dry_run": dry_run or not write,
                }
            )
            if write and not dry_run:
                repo.save_path(out_path, raw)
        except Exception as exc:  # noqa: BLE001 — continue campaign batch
            fail += 1
            reports.append(
                {
                    "article": num,
                    "ok": False,
                    "error": str(exc),
                    "path": str(out_path if out_path.is_file() else path),
                }
            )

    typer.echo(
        json.dumps(
            {
                "ok": fail == 0,
                "source": mfr.slug,
                "tag": import_tag,
                "count": len(reports),
                "fail": fail,
                "skipped": skipped,
                "appended": appended,
                "results": reports,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if fail:
        raise typer.Exit(code=1)
