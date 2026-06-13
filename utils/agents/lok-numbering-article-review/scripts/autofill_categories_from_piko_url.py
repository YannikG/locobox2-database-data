#!/usr/bin/env python3
"""
Set ``categories`` from PIKO shop ``source.url`` (and first description line) when empty.

Only fills when ``categories`` is empty (or missing) and the URL is a clear PIKO shop
article slug (``dampflok-``, ``diesellok-``, ``e-lok-``, ``elektotriebwagen-`` (PIKO-Schreibweise),
``zweikraftlok-``, ``dieseltriebzug-``, ``elektrotriebzug-``, ``zugset-``, ``start-set-``, …).

Usage (repo root)::

    .venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofill_categories_from_piko_url.py articles/piko
    .venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofill_categories_from_piko_url.py --apply articles/piko
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


def _blob(url: str, description: str, model_type: str = "") -> str:
    first = (description or "").split("\n", 1)[0].lower()
    mt = (model_type or "").strip().lower()
    return f"{url.lower()} {first} {mt}"


def _lok_subtype_from_power(b: str) -> Optional[str]:
    """Zweite Kategorie für Lokomotiven aus Antriebs-Hinweisen im Slug/Titel."""
    if "zweikraftlok" in b or "dual-mode" in b or "dual mode" in b:
        return "elektrolokomotive"
    if "dampflok" in b or "schlepptenderlok" in b:
        return "dampflokomotive"
    if "diesellok" in b:
        return "diesellokomotive"
    if (
        "e-lok" in b
        or "elektrolok" in b
        or "sound-e-lok" in b
        or re.search(r"\bbr\s*\d+", b)
        or "eu44" in b
        or "metropolitan" in b
    ):
        return "elektrolokomotive"
    return None


def _categories_from_piko(url: str, description: str = "", model_type: str = "") -> Optional[list[str]]:
    u = url.lower()
    if "piko-shop.de" not in u and "piko.de" not in u:
        return None

    b = _blob(url, description, model_type)

    if "dieseltriebwagen" in b or "sound-dieseltriebwagen" in u:
        return ["lokomotive", "dieseltriebwagen"]
    if (
        "sound-e-triebwagen" in u
        or "e-triebwagen" in u
        or "elektrotriebwagen" in b
        or "elektotriebwagen" in b
        or "n-triebwagen" in u
        or re.search(r"(?<![a-z])triebwagen", b)
    ):
        return ["lokomotive", "triebzug"]
    if "dieseltriebzug" in b or "elektrotriebzug" in b or "sound-elektrotriebzug" in u:
        return ["lokomotive", "triebzug"]
    if "triebzug" in b and "triebwagen" not in b:
        return ["lokomotive", "triebzug"]
    if "schienenbus" in b:
        return ["lokomotive", "triebzug"]

    if "zugset" in b or "start-set" in b or "start-set" in u or "start_set" in b:
        sub = _lok_subtype_from_power(b)
        if sub:
            return ["lokomotive", sub]
        return None

    sub = _lok_subtype_from_power(b)
    if sub:
        return ["lokomotive", sub]

    return None


def _walk(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = raw if raw.is_absolute() else Path.cwd() / raw
        if p.is_file() and p.suffix == ".json":
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(p.rglob("*.json")))
        else:
            print(f"error: not found: {p}", file=sys.stderr)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path, default=[Path("articles/piko")])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    changed: list[tuple[Path, list[str]]] = []
    skipped: list[tuple[Path, str]] = []

    for path in _walk(args.paths):
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: {path}: {e}", file=sys.stderr)
            return 1

        cats = data.get("categories")
        if cats is not None and len(cats) > 0:
            continue

        url = ((data.get("source") or {}).get("url") or "").strip()
        if not url:
            skipped.append((path, "no source.url"))
            continue

        desc = data.get("description") or ""
        model_type = ((data.get("model") or {}).get("type") or "").strip()
        new_cats = _categories_from_piko(url, desc, model_type)
        if not new_cats:
            skipped.append((path, "url/description not a known PIKO lok class"))
            continue

        changed.append((path, new_cats))
        if args.apply:
            data["categories"] = new_cats
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    for p, nc in changed:
        print(f"{p}\t{nc}")

    if skipped and not args.apply:
        for p, reason in skipped[:30]:
            print(f"skip\t{p}\t{reason}", file=sys.stderr)
        if len(skipped) > 30:
            print(f"skip\t…\t{len(skipped) - 30} more", file=sys.stderr)

    if changed:
        msg = f"{len(changed)} file(s) {'updated' if args.apply else 'would update'}."
        print(msg, file=sys.stderr)
    else:
        print("No matching empty-category files.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
