#!/usr/bin/env python3
"""
Set ``categories`` from Roco shop ``source.url`` when currently empty.

Only fills when ``categories`` is empty (or missing) and ``source.url`` is a
clear Roco shop URL: path under ``…/lokomotiven/{dampf|diesel|elektro}lokomotiven/``,
``…/lokomotiven/triebzuge/``, or ``…/home-neuheiten/…`` with a matching product
slug (e.g. ``-dampflokomotive-``). Skips wagons, unknown slugs, non-Roco hosts.

Usage (repo root)::

    python3 utils/agents/lok-numbering-article-review/scripts/autofill_categories_from_roco_url.py articles/roco
    python3 utils/agents/lok-numbering-article-review/scripts/autofill_categories_from_roco_url.py --apply articles/roco
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional


def _categories_from_url(url: str) -> Optional[list[str]]:
    u = url.lower()
    if "roco.cc" not in u:
        return None
    if "/dampflokomotiven/" in u:
        return ["lokomotive", "dampflokomotive"]
    if "/diesellokomotiven/" in u:
        return ["lokomotive", "diesellokomotive"]
    if "/elektrolokomotiven/" in u:
        return ["lokomotive", "elektrolokomotive"]
    if "/triebzuge/" in u:
        return ["lokomotive", "triebzug"]
    if "/home-neuheiten/" in u:
        if "-dampflokomotive-" in u or "dampflokomotive-" in u.split("/")[-1]:
            return ["lokomotive", "dampflokomotive"]
        if "-diesellokomotive-" in u:
            return ["lokomotive", "diesellokomotive"]
        if "-elektrolokomotive-" in u:
            return ["lokomotive", "elektrolokomotive"]
        if "-elektrotriebzug-" in u or "-triebzug-" in u or "akkutriebwagen-" in u:
            return ["lokomotive", "triebzug"]
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
    ap.add_argument("paths", nargs="*", type=Path, default=[Path("articles/roco")])
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

        new_cats = _categories_from_url(url)
        if not new_cats:
            skipped.append((path, "url not a known lokomotiven class path"))
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
        for p, reason in skipped:
            print(f"skip\t{p}\t{reason}", file=sys.stderr)

    if changed:
        msg = f"{len(changed)} file(s) {'updated' if args.apply else 'would update'}."
        print(msg, file=sys.stderr)
    else:
        print("No matching empty-category files.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
