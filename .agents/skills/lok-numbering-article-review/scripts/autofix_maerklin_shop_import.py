#!/usr/bin/env python3
"""
Autofix Märklin-PDP-Reste bei Triebwagen/Lok-Titeln (Allowlist, konservativ).

- ``model.type``: Produktklassen-Präfix («Schwere Güterzug-Elektrolokomotive BR 194»,
  «Nahverkehrs-Dieseltriebwagen LINT 41») → Rest («BR 194», «LINT 41»). Nur wenn der
  Rest eine Ziffer enthält; sonst unverändert (Finding in Pass 1).
- Laufnummer am Ende des Typs («BR 18 505» bei ``number`` 505) wird abgeschnitten.
- Kaputter Typ (Satzfragment «der bayerischen Gattung S 2/6.», «mit Heizkamin.», «Nr.», «.»,
  nur Produktklasse «Dieselelektrische Lokomotive.», UIC-Nummer) → Bezeichnung aus dem
  ersten Vorbild-Satz («Baureihe X» → «BR X», «Reihe/Serie X», «EMD F7»). Ohne klaren Treffer
  bleibt der Typ unverändert (Finding in Pass 1).
- ``model.number``: wenn ``null`` und die Vorbild-Beschreibung «(Lok-)Betriebsnummer N» /
  «Loknummer N» nennt: nur eindeutige Fälle (EVN-artig «327-1» hinter der Baureihe, kurze
  Ziffernnummer wie 4410/5641). Keine Ratefälle («6306 MAINZ», «als ICE 786»).

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
    r"kleinlokomotive|rangierlokomotive|doppellokomotive|lok|hochgeschwindigkeitszug)\b",
    re.I,
)


_BAD_TYPE = re.compile(
    r"^(?:der|des|mit|zum|zur|in|nach|ex)\b|^(?:Nr|No)\.?$|^\W*$|Doppeltraktion|Doppeleinheit|"
    r"Dieselelektrische\s+Lokomotive|Dieselhydraulische\s+\w*lokomotive|\bNr\.?$",
    re.I,
)
_UIC_LIKE = re.compile(r"^\d{2}\s\d{2}\s\d{4}\s")
_DESIG = re.compile(
    r"\b(?P<kw>Baureihe|BR|Reihe|Serie|Gattung|Klasse|Class)\s+(?P<v>[A-Z0-9][\w.\-/]*(?:\s[\w.\-/]+){0,2}?)"
    r"(?=\s+(?:der|des|von|mit|in|als|aus|und|ex|zu|für|im|am|auf)\b|\s*[(,;]|\.(?:\s|$)|$)"
)
_EMD = re.compile(r"EMD\s+F\s?7")


def norm_series(t: str) -> str:
    """Swiss class «Serie Be 6/8 II» → «Be 6/8 II» (numeric «Serie 1100» stays)."""
    return re.sub(r"^(?:Serie|Reihe|Gattung)\s+(?=[A-Z][A-Za-z]{0,3}\s\d+/\d)", "", t)


def is_bad_type(t: str) -> bool:
    s = t.strip()
    if _BAD_TYPE.search(s) or _UIC_LIKE.match(s):
        return True
    if re.fullmatch(r"[\w\-]*(?:lokomotive|lok|triebzug|triebwagen)\.?", s, re.I):
        return True
    return False


def type_from_vorbild(desc: str) -> str | None:
    vor = re.sub(r"^Vorbild:\s*", "", desc.split("Modell:", 1)[0].strip())
    first = re.split(r"(?<=\.)\s+(?=[A-ZÄÖÜ])", vor, maxsplit=1)[0]
    if _EMD.search(first):
        return "EMD F7"
    m = _DESIG.search(first)
    if not m:
        return None
    kw, v = m.group("kw"), m.group("v").strip(" .")
    toks = v.split()
    while len(toks) > 1 and re.fullmatch(r"[A-Za-zÄÖÜäöü]{3,}", toks[-1]) and not re.fullmatch(r"[IVX]+", toks[-1]):
        toks.pop()
    v = " ".join(toks)
    if re.search(r"[a-z]{4,}", v) or not (re.search(r"\d", v) or len(toks[0]) <= 3):
        return None
    if re.match(r"(?:T?VT|ER)\b", v):
        return v
    if kw in ("Baureihe", "BR"):
        return f"BR {v}"
    if kw == "Gattung":
        return v
    return norm_series(f"{kw} {v}")


def number_from_vorbild(desc: str, typ: str) -> str | None:
    vor = desc.split("Modell:", 1)[0]
    m = re.search(
        r"(?:Lok-?Betriebsnummer|Betriebsnummer|Loknummer|Lok-Nummer)\s+([A-Z0-9][\w.\-/ ]{1,16}?)(?=[.,;]\s|[.,;]$|\s+(?:und|als|in)\b|$)",
        vor,
    )
    if not m:
        return None
    n = m.group(1).strip()
    bare = re.sub(r"^(?:BR|Rh|Baureihe)\s+", "", typ)
    if n.lower().startswith(bare.lower() + " ") and bare:
        n = n[len(bare) :].strip()
    elif re.fullmatch(r"\d{3}\s\d{3}-\d", n):
        n = n.split(" ", 1)[1]
    if re.fullmatch(r"\d{3}-\d|\d{2,5}", n) and n != bare and not re.fullmatch(r"20\d\d", n):
        return n
    return None


def new_type(t: str, number: str | None) -> str | None:
    s = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    s = re.split(r",| - | – ", s, maxsplit=1)[0].strip()
    matches = list(_CLASS_WORD.finditer(s))
    if not matches:
        return None
    rest = s[matches[-1].end() :].strip()
    rest = re.split(r"\s+als\s+", rest, flags=re.I)[-1]
    rest = re.sub(
        r"^mit\s+\S+\s+(?=(?:BR|Baureihe|Reihe|Serie|Gattung|Klasse|Class)\b)", "", rest, flags=re.I
    )
    rest = re.sub(r"^(?:als|mit)\s+", "", rest, flags=re.I)
    rest = re.sub(r"\s+mit\s+.*$", "", rest, flags=re.I)
    rest = re.sub(r"^Baureihe\s+", "BR ", rest, flags=re.I)
    rest = re.sub(r"^BR\s+(?=VT\b)", "", rest)
    rest = re.sub(r"^Gattung\s+(?=[A-Z]\s?\d)", "", rest)
    rest = rest.rstrip(". ").strip()
    if re.fullmatch(r"Köf\s+II", rest):
        return "Köf II"
    hgz = re.match(r"hochgeschwindigkeitszug\b", s, re.I) and re.fullmatch(r"(?:ICE|TGV|Velaro)\b.*", rest)
    if not rest or not (re.search(r"\d", rest) or hgz):
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
        desc = d.get("description") or ""
        if is_bad_type(t) or (nt is None and t.rstrip().endswith(".")):
            alt = type_from_vorbild(desc)
            if alt:
                nt = alt
        elif nt is None and t.endswith("."):
            nt = t.rstrip(". ")
        if nt and nt != t:
            print(f"{p}\ttype {t!r} -> {nt!r}")
            changed += 1
            if args.apply:
                m["type"] = nt
        ns = norm_series(m.get("type") or "")
        if ns != (m.get("type") or ""):
            print(f"{p}\ttype {m.get('type')!r} -> {ns!r}")
            changed += 1
            if args.apply:
                m["type"] = ns
        typ = m.get("type") or ""
        if m.get("number") is None and typ and not is_bad_type(typ):
            nn = number_from_vorbild(desc, typ)
            if nn:
                print(f"{p}\tnumber None -> {nn!r}")
                changed += 1
                if args.apply:
                    m["number"] = nn
        if args.apply:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{'Updated' if args.apply else 'Would update'} {changed} file(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
