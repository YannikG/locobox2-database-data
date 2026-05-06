#!/usr/bin/env python3
"""
Replace common OCR / encoding glitches in article ``description`` only.

Never touches ``source.url``, ``model.*``, or other fields. Idempotent where
possible. Run from repo root.

  python3 utils/agents/lok-numbering-article-review/scripts/autofix_description_ocr.py articles/roco
  python3 utils/agents/lok-numbering-article-review/scripts/autofix_description_ocr.py --apply articles/roco
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Order: longer / more specific first where relevant.
_REPLACEMENTS: list[tuple[str, str]] = [
    ("Fiihrerstandsriickwand", "Führerstandsrückwand"),
    ("Fiihrerstandsrückwand", "Führerstandsrückwand"),
    ("Fihrerstandsriickwand", "Führerstandsrückwand"),
    ("Fiihrerstandsbeleuchtung", "Führerstandsbeleuchtung"),
    ("Fiihrerstands-", "Führerstands-"),
    ("Fiihrerstands.", "Führerstands."),
    ("Fiihrer-", "Führer-"),
    ("Fiihrer.", "Führer."),
    ("Fiihrer", "Führer"),
    ("Fihrerstands", "Führerstands"),
    ("Fihrer", "Führer"),
    ("Riickwand", "Rückwand"),
    ("riickwand", "rückwand"),
    ("Ausfiihrung", "Ausführung"),
    ("Ausfiihr", "Ausführ"),
    ("ausgefiihrt", "ausgeführt"),
    ("ausgefiihr", "ausgeführ"),
    ("verfiigt", "verfügt"),
    ("verfiig", "verfüg"),
    ("Atztechnik", "Ätztechnik"),
    ("Atzteilen", "Ätzteilen"),
    ("Atz-", "Ätz-"),
    ("Urspriinglich", "Ursprünglich"),
    ("Urspriing", "Ursprüng"),
    ("Uberwiegend", "Überwiegend"),
    ("Uber ", "Über "),
    ("Uber.", "Über."),
    ("gegrundet", "gegründet"),
    ("Guterzugverkehr", "Güterzugverkehr"),
    ("Guterzug", "Güterzug"),
    ("Giiterz", "Güterz"),
    ("Giiter", "Güter"),
    ("Schienenraumer", "Schienenräumer"),
    ("Schalldampfer", "Schalldämpfer"),
    ("Vollstandige", "Vollständige"),
    ("Vollstandig", "Vollständig"),
    ("vollstandig", "vollständig"),
    ("GroBteil", "Grossteil"),
    ("GroBen", "Grossen"),
    ("groBen", "grossen"),
    ("Osterreich", "Österreich"),
    (" spater ", " später "),
    (" spater.", " später."),
    ("Spater ", "Später "),
    ("Spater.", "Später."),
    (" fiir ", " für "),
    (" fiir.", " für."),
    (" fir ", " für "),  # OCR without dots on i
    ("Siiddeutschland", "Süddeutschland"),
    ("Siid", "Süd"),
    ("Anderungen", "Änderungen"),
    ("Deutsche. Reichsbahn", "Deutsche Reichsbahn"),
    ("Giterwagen", "Güterwagen"),
    ("Bahnhofen", "Bahnhöfen"),
    (" bereits fruh ", " bereits früh "),
    (" bereits fruh.", " bereits früh."),
    ("zunachst", "zunächst"),
    ("prasentiert", "präsentiert"),
    ("ausgerUstet", "ausgerüstet"),
    ("ermdglichen", "ermöglichen"),
    ("K6f", "Köf"),
    ("Kéf", "Köf"),
    ("Kraftiibertragung", "Kraftübertragung"),
    (" tiber ", " über "),
    ("Fur ", "Für "),
    ("Fur den", "Für den"),
    ("Verfugung", "Verfügung"),
    ("Verflgung", "Verfügung"),
    ("Fruhjahr", "Frühjahr"),
    ("Beforderung", "Beförderung"),
    ("Zige ", "Züge "),
    ("Zige.", "Züge."),
    ("Ausfuhrung", "Ausführung"),
    ("ab. Werk", "ab Werk"),
    ("eckigemTürausschnitt", "eckigem Türausschnitt"),
    ("Führer-. standsbeleuchtung", "Führerstandsbeleuchtung"),
    ("Führer-. stands", "Führerstands"),
    ("Maschinen-. raumbeleuchtung", "Maschinenraumbeleuchtung"),
    ("Schluss-. licht", "Schlusslicht"),
    ("Schlusslicht. und", "Schlusslicht und"),
    (",,Taigatrommel\"", "«Taigatrommel»"),
    (",,Taigatrommel", "«Taigatrommel»"),
]


def _apply(desc: str) -> str:
    s = desc
    for old, new in _REPLACEMENTS:
        s = s.replace(old, new)
    return s


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

    changed: list[tuple[Path, int]] = []
    for path in _walk(args.paths):
        try:
            text = path.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(text)
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: {path}: {e}", file=sys.stderr)
            return 1
        desc = data.get("description")
        if not isinstance(desc, str) or not desc:
            continue
        new_desc = _apply(desc)
        if new_desc == desc:
            continue
        changed.append((path, len(desc) - len(new_desc)))
        if args.apply:
            data["description"] = new_desc
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    for p, _ in changed:
        print(p)
    if changed:
        print(f"\n{len(changed)} file(s) {'updated' if args.apply else 'would change'}.", file=sys.stderr)
    else:
        print("No OCR pattern matches.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
