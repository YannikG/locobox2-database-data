#!/usr/bin/env python3
"""
Aus einer Artikelliste (eine 5–8 stellige Nummer pro Zeile, ``#`` Kommentare):
fehlende ``articles/roco/{nr}.json`` als **Stub** anlegen. Bestehende Dateien werden **nicht**
überschrieben.

Beispiel (Repo-Root)::

    python3 utils/roco/shop-pdp-parse/roco_catalogue_stub.py --articles .tmp/roco-neuheiten-nrs.txt

Optional: ``--fail-if-nothing-created`` (Exit 1, wenn ``created == 0``), ``--dry-run``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ARTICLES_ROOT = _REPO_ROOT / "articles" / "roco"


def _read_article_numbers(path: Path) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.isdigit() and 5 <= len(line) <= 8:
            if line not in seen:
                seen.add(line)
                out.append(line)
        else:
            print(f"warning: Zeile übersprungen: {line!r}", file=sys.stderr)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fehlende articles/roco/*.json aus Nummernliste als Stub anlegen (kein Überschreiben).",
    )
    ap.add_argument(
        "--articles",
        type=Path,
        required=True,
        metavar="PATH",
        help="Textdatei: eine Artikelnummer pro Zeile (5–8 Ziffern), # Kommentare.",
    )
    ap.add_argument(
        "--articles-root",
        type=Path,
        default=_DEFAULT_ARTICLES_ROOT,
        help=f"Zielverzeichnis (default: {_DEFAULT_ARTICLES_ROOT}).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur zählen/ausgeben, keine Dateien schreiben.",
    )
    ap.add_argument(
        "--fail-if-nothing-created",
        action="store_true",
        help="Exit-Code 1, wenn nach dem Lauf keine neue Datei angelegt wurde (created == 0).",
    )
    args = ap.parse_args()

    p = args.articles.expanduser().resolve()
    if not p.is_file():
        print(f"error: Datei fehlt: {p}", file=sys.stderr)
        return 2

    import roco_shop_parse_pdp as pdp

    root = args.articles_root.expanduser().resolve()
    numbers = _read_article_numbers(p)
    if not numbers:
        print("error: keine gültigen Artikelnummern in der Liste.", file=sys.stderr)
        return 2

    created = 0
    skipped = 0
    for art in numbers:
        out_path = root / f"{art}.json"
        if out_path.is_file():
            skipped += 1
            continue
        if args.dry_run:
            print(f"would create {out_path}")
            created += 1
            continue
        root.mkdir(parents=True, exist_ok=True)
        stub = pdp.article_record_stub(art)
        out_path.write_text(
            json.dumps(stub, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        created += 1

    print(
        json.dumps(
            {"created": created, "skipped_existing": skipped},
            ensure_ascii=False,
        )
    )
    if args.fail_if_nothing_created and created == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
