from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_tag_slug(raw: str) -> str:
    s = (raw or "").strip().lower().replace("_", "-")
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s or not _SLUG_RE.fullmatch(s):
        raise ValueError(
            f"invalid tag slug {raw!r}; expected kebab-case like piko-neuheiten-2024"
        )
    return s


def default_tag_name(slug: str) -> str:
    parts = slug.split("-")
    out: list[str] = []
    for p in parts:
        if p.isdigit() or re.fullmatch(r"20\d{2}", p):
            out.append(p)
        elif p in {"piko", "roco", "db", "sbb", "oebb"}:
            out.append(p.upper() if p != "oebb" else "ÖBB")
        else:
            out.append(p[:1].upper() + p[1:])
    return " ".join(out)


@dataclass(frozen=True, slots=True)
class TagTaxonomy:
    repo_root: Path

    @property
    def tags_dir(self) -> Path:
        return self.repo_root / "config" / "tags"

    def path_for(self, slug: str) -> Path:
        return self.tags_dir / f"{normalize_tag_slug(slug)}.json"

    def exists(self, slug: str) -> bool:
        return self.path_for(slug).is_file()

    def require(self, slug: str) -> str:
        s = normalize_tag_slug(slug)
        if not self.exists(s):
            raise FileNotFoundError(
                f"unknown tag {s!r}: missing config/tags/{s}.json. "
                f"Run: uv run locobox tags ensure --slug {s}"
            )
        return s

    def ensure(
        self,
        slug: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        kind: Optional[str] = None,
        manufacturer_slug: Optional[str] = None,
        year: Optional[int] = None,
        order: Optional[int] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        s = normalize_tag_slug(slug)
        path = self.path_for(s)
        if path.is_file():
            return {
                "ok": True,
                "created": False,
                "slug": s,
                "path": str(path),
                "dry_run": dry_run,
            }
        payload: dict[str, Any] = {
            "schemaVersion": "1.0.0",
            "name": (name or "").strip() or default_tag_name(s),
            "slug": s,
            "description": (description or "").strip()
            or f"Import-Kampagne {s}.",
        }
        kind_norm = (kind or "").strip()
        if kind_norm:
            payload["kind"] = kind_norm
        mfr = (manufacturer_slug or "").strip().lower()
        if mfr:
            payload["manufacturerSlug"] = mfr
        if year is not None:
            payload["year"] = int(year)
        if order is not None:
            payload["order"] = int(order)
        if not dry_run:
            self.tags_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return {
            "ok": True,
            "created": True,
            "slug": s,
            "path": str(path),
            "dry_run": dry_run,
            "tag": payload,
        }


@dataclass(frozen=True, slots=True)
class AppendTagResult:
    article: str
    path: str
    ok: bool
    changed: bool
    skipped: bool
    error: Optional[str] = None
    tags: Optional[list[str]] = None


@dataclass(frozen=True, slots=True)
class AppendArticleTag:
    """Append a taxonomy tag to an existing article JSON (idempotent)."""

    repo_root: Path

    def run_one(
        self,
        article: dict[str, Any],
        tag: str,
        *,
        article_number: str,
        path: Path,
    ) -> tuple[dict[str, Any], AppendTagResult]:
        from locobox_cli.application.articles.validate import ValidateArticle

        slug = TagTaxonomy(self.repo_root).require(tag)
        tags = list(article.get("tags") or [])
        if slug in tags:
            return article, AppendTagResult(
                article=article_number,
                path=str(path),
                ok=True,
                changed=False,
                skipped=True,
                tags=tags,
            )
        new_tags = [*tags, slug]
        data = deepcopy(article)
        data["tags"] = new_tags
        data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ValidateArticle.from_contracts(self.repo_root).assert_valid(data)
        return data, AppendTagResult(
            article=article_number,
            path=str(path),
            ok=True,
            changed=True,
            skipped=False,
            tags=new_tags,
        )
