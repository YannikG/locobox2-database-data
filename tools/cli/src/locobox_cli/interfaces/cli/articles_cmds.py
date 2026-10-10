from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import typer

from locobox_cli.adapters.article_fs import FilesystemArticleRepository
from locobox_cli.adapters.paths import find_repo_root
from locobox_cli.application.articles.patch import (
    PatchArticle,
    SetField,
    append_audit_log,
    load_patch_jsonl,
    parse_value_arg,
)
from locobox_cli.application.articles.validate import ValidateArticle
from locobox_cli.application.queue.parse import parse_queue_text
from locobox_cli.application.tags.taxonomy import AppendArticleTag, TagTaxonomy
from locobox_cli.domain.manufacturer import Manufacturer

app = typer.Typer(
    help="Article JSON: validate, set-field, patch, append-tag.",
    no_args_is_help=True,
)


def _audit_path(root: Path) -> Path:
    return root / ".tmp" / "article-patch-audit.jsonl"


@app.command("validate")
def validate_cmd(
    file: Optional[Path] = typer.Option(None, "--file", "-f"),
    manufacturer: Optional[str] = typer.Option(None, "--mfr", "-m"),
    article: Optional[str] = typer.Option(None, "--article", "-a"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Validate one article against contracts/article.schema.json."""
    root = repo_root or find_repo_root()
    repo = FilesystemArticleRepository(root)
    mfr = Manufacturer.parse(manufacturer) if manufacturer else None
    path = repo.resolve_article_file(path=file, manufacturer=mfr, article_number=article)
    data = repo.load_path(path)
    issues = ValidateArticle.from_contracts(root).run(data)
    if not issues:
        typer.echo(json.dumps({"ok": True, "file": str(path)}, ensure_ascii=False))
        return
    payload = {
        "ok": False,
        "file": str(path),
        "issues": [{"path": i.path, "message": i.message} for i in issues],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    raise typer.Exit(code=1)


@app.command("set-field")
def set_field_cmd(
    path: str = typer.Option(..., "--path", "-p", help="Dot path, e.g. model.type"),
    value: str = typer.Option(..., "--value", "-v"),
    file: Optional[Path] = typer.Option(None, "--file", "-f"),
    manufacturer: Optional[str] = typer.Option(None, "--mfr", "-m"),
    article: Optional[str] = typer.Option(None, "--article", "-a"),
    as_json: bool = typer.Option(False, "--json", help="Parse --value as JSON"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    audit: bool = typer.Option(True, "--audit/--no-audit"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Set one allowed field; schema-validate before write."""
    root = repo_root or find_repo_root()
    repo = FilesystemArticleRepository(root)
    mfr = Manufacturer.parse(manufacturer) if manufacturer else None
    art_path = repo.resolve_article_file(path=file, manufacturer=mfr, article_number=article)
    data = repo.load_path(art_path)
    parsed: Any = parse_value_arg(value, as_json=as_json)
    result = SetField(ValidateArticle.from_contracts(root)).run(data, path, parsed)
    payload = {
        "file": str(art_path),
        "path": result.path,
        "before": result.before,
        "after": result.after,
        "dry_run": dry_run,
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    if dry_run:
        return
    repo.save_path(art_path, result.article)
    if audit:
        append_audit_log(
            _audit_path(root),
            {
                "op": "set-field",
                "file": str(art_path),
                "path": result.path,
                "before": result.before,
                "after": result.after,
            },
        )


@app.command("patch")
def patch_cmd(
    changes: Path = typer.Option(..., "--file", "-f", help="JSONL of patch ops"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    audit: bool = typer.Option(True, "--audit/--no-audit"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Batch patch from JSONL; each article validated after its changes."""
    root = repo_root or find_repo_root()
    repo = FilesystemArticleRepository(root)
    validator = ValidateArticle.from_contracts(root)
    patcher = PatchArticle(validator)

    # group by article key
    grouped: dict[str, list[tuple[str, Any]]] = {}
    order: list[str] = []
    for key, field_path, val in load_patch_jsonl(changes):
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append((field_path, val))

    reports: list[dict[str, Any]] = []
    for key in order:
        if key.startswith("articles/") or key.endswith(".json"):
            art_path = (root / key).resolve() if not Path(key).is_absolute() else Path(key)
        else:
            mfr_s, _, num = key.partition(":")
            art_path = repo.article_path(Manufacturer.parse(mfr_s), num)
        data = repo.load_path(art_path)
        new_data, results = patcher.run(data, grouped[key])
        report = {
            "file": str(art_path),
            "changes": [{"path": r.path, "before": r.before, "after": r.after} for r in results],
            "dry_run": dry_run,
        }
        reports.append(report)
        if not dry_run:
            repo.save_path(art_path, new_data)
            if audit:
                append_audit_log(
                    _audit_path(root),
                    {"op": "patch", "file": str(art_path), "changes": report["changes"]},
                )

    typer.echo(json.dumps({"ok": True, "articles": reports}, ensure_ascii=False, indent=2))


@app.command("append-tag")
def append_tag_cmd(
    tag: str = typer.Option(..., "--tag", help="Taxonomy tag slug"),
    manufacturer: str = typer.Option(..., "--mfr", "-m"),
    article: Optional[str] = typer.Option(None, "--article", help="Single article number"),
    articles: Optional[Path] = typer.Option(
        None, "--articles", "-a", help="Queue .txt with article numbers"
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
    repo_root: Optional[Path] = typer.Option(None, "--repo-root"),
) -> None:
    """Append a tag to existing article JSON (idempotent; no shop overwrite)."""
    root = repo_root or find_repo_root()
    mfr = Manufacturer.parse(manufacturer)
    try:
        slug = TagTaxonomy(root).require(tag)
    except (ValueError, FileNotFoundError) as exc:
        typer.echo(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise typer.Exit(code=1) from exc

    nums: list[str] = []
    if article:
        nums.append(article.strip())
    if articles:
        nums.extend(e.article.value for e in parse_queue_text(articles.read_text(encoding="utf-8")).entries)
    # dedupe preserve order
    seen: set[str] = set()
    ordered: list[str] = []
    for n in nums:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    if not ordered:
        raise typer.BadParameter("provide --article and/or --articles")

    repo = FilesystemArticleRepository(root)
    appender = AppendArticleTag(root)
    reports: list[dict[str, Any]] = []
    fail = 0
    changed = 0
    for num in ordered:
        path = repo.article_path(mfr, num)
        if not path.is_file():
            fail += 1
            reports.append(
                {"article": num, "ok": False, "error": "article_missing", "path": str(path)}
            )
            continue
        try:
            data = repo.load_path(path)
            new_data, result = appender.run_one(
                data, slug, article_number=num, path=path
            )
            if result.changed:
                changed += 1
                if not dry_run:
                    repo.save_path(path, new_data)
            reports.append(
                {
                    "article": num,
                    "ok": True,
                    "changed": result.changed,
                    "skipped": result.skipped,
                    "tags": result.tags,
                    "file": str(path),
                    "dry_run": dry_run,
                }
            )
        except Exception as exc:  # noqa: BLE001
            fail += 1
            reports.append({"article": num, "ok": False, "error": str(exc), "path": str(path)})

    typer.echo(
        json.dumps(
            {
                "ok": fail == 0,
                "tag": slug,
                "count": len(reports),
                "changed": changed,
                "fail": fail,
                "results": reports,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if fail:
        raise typer.Exit(code=1)
