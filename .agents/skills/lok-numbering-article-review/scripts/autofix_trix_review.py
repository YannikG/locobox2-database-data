#!/usr/bin/env python3
"""
Review-Autofix für Trix-/Märklin-Produktdatenbank-Importe (nur ``model.type``, Allowlist).

Läuft **nach** ``autofix_trix_shop_import.py`` und ``autofix_maerklin_shop_import.py``:

- Zusatz nach Komma/Design: «BR 185 im Design für den Film», «Köf II, zugelassen bei der DB» → Kern.
- Klassenwort vor Bauart/Gattung: «Nassdampflokomotive Gattung D XI» → «D XI»,
  «Kleinlokomotive Bauart Köf II.» → «Köf II», «Dampftriebwagen Bauart Kittel CidT» → «Kittel CidT».
- ``BR`` vor Länderbahn-/Sondergattungen entfernen (``BR EP 3/6`` → ``EP 3/6``, ``BR SVT 04`` → ``SVT 04``,
  ``BR Köf II`` → ``Köf II``).
- ``Bauart``/``Reihe``/``Serie``/``Gattung`` vor Buchstaben-Bezeichnungen entfernen
  (``Reihe RAm TEE I 501`` → ``RAm TEE I``, ``Serie RAe TEE II`` → ``RAe TEE II``); rein numerische
  Reihen («Reihe 2016», «Serie 1200») bleiben.
- «bis» in Nummernbereichen → Bindestrich («DE 1001 bis 1003» → «DE 1001-1003»).

Usage::

    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_trix_review.py [--apply] articles/trix/*.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def clean_type(t: str) -> str:
    s = t.strip()
    s = re.sub(r",?\s+(?:im\s+Design|zugelassen\s+bei)\b.*$", "", s)
    s = re.sub(r"\s+und\s+\d+$", "", s)
    s = re.sub(
        r"^[A-Za-zÄÖÜäöüß\-]*(?:lokomotive|lok|triebwagen)\.?\s+(?:Bauart|Gattung|Reihe|Serie|Typ)\s+",
        "",
        s,
    )
    s = re.sub(r"^(?:Bauart|Gattung)\s+(?=[A-Z])", "", s)
    s = re.sub(r"^(?:Reihe|Serie)\s+(?=[A-Z][A-Za-z]{0,3}(?:\s|$))", "", s)
    s = re.sub(r"^BR\s+(?=(?:EP|SVT|Köf)\b)", "", s)
    s = re.sub(r"^BR\s+(?=[A-Z][A-Za-z]{0,2}\s\d+/\d)", "", s)
    s = re.sub(r"^(\D+?\s\d+)\s+bis\s+(\d+)$", r"\1-\2", s)
    return s.rstrip(". ").strip() or t


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args(argv)
    changed = 0
    for p in args.paths:
        d = json.loads(p.read_text(encoding="utf-8"))
        m = d.get("model", {})
        t = m.get("type") or ""
        nt = clean_type(t)
        if nt != t:
            print(f"{p}\ttype {t!r} -> {nt!r}")
            changed += 1
            if args.apply:
                m["type"] = nt
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{'Updated' if args.apply else 'Would update'} {changed} file(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
