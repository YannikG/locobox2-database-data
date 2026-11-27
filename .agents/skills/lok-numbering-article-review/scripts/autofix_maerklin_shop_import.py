#!/usr/bin/env python3
"""
Autofix Märklin-PDP-Reste bei Triebwagen/Lok-Titeln (Allowlist, konservativ).

- ``model.type``: Produktklassen-Präfix («Schwere Güterzug-Elektrolokomotive BR 194»,
  «Nahverkehrs-Dieseltriebwagen LINT 41») → Rest («BR 194», «LINT 41»). Nur wenn der
  Rest eine Ziffer enthält; sonst unverändert (Finding in Pass 1).
- Laufnummer am Ende des Typs («BR 18 505» bei ``number`` 505) wird abgeschnitten.

Usage::

    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_maerklin_shop_import.py [--apply] articles/maerklin/*.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_CLASS_WORD = re.compile(
    r"(?:lokomotive|lokomotiven|triebwagen|triebwagenzug|triebzug|schnelltriebwagen|"
    r"kleinlokomotive|rangierlokomotive|doppellokomotive|lok)\b",
    re.I,
)


def new_type(t: str, number: str | None) -> str | None:
    s = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    s = re.split(r",| - | – ", s, maxsplit=1)[0].strip()
    matches = list(_CLASS_WORD.finditer(s))
    if not matches:
        return None
    rest = s[matches[-1].end() :].strip()
    rest = re.split(r"\s+als\s+", rest, flags=re.I)[-1]
    rest = re.sub(r"^(?:als|mit)\s+", "", rest, flags=re.I)
    rest = re.sub(r"\s+mit\s+.*$", "", rest, flags=re.I)
    rest = re.sub(r"^Baureihe\s+", "BR ", rest, flags=re.I)
    rest = re.sub(r"^BR\s+(?=VT\b)", "", rest)
    if not rest or not re.search(r"\d", rest):
        return None
    if number:
        rest = re.sub(rf"\s+{re.escape(number)}$", "", rest)
    return rest.strip() or None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    changed = 0
    for p in map(Path, args.paths):
        d = json.loads(p.read_text(encoding="utf-8"))
        m = d.get("model", {})
        t = m.get("type") or ""
        nt = new_type(t, m.get("number"))
        if nt and nt != t:
            print(f"{p}\t{t!r} -> {nt!r}")
            changed += 1
            if args.apply:
                m["type"] = nt
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{'Updated' if args.apply else 'Would update'} {changed} file(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
