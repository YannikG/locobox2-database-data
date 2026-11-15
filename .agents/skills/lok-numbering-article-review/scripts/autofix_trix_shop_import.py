#!/usr/bin/env python3
"""
Autofix Trix Produktdatenbank-Importreste (Allowlist, konservativ).

- ``model.type``: Shop-Präfixe (Dampflokomotive / Baureihe …) → ``BR …`` / Bauart;
  Sondernamen in Anführungszeichen → ``model.livery`` wenn noch leer.
- ``model.number``: aus ``Betriebsnummer`` / ``Lok-Betriebsnummer`` in der Beschreibung,
  wenn ``number`` noch null und eindeutig.
- ``categories``: Parent ``lokomotive`` plus Dampf/Diesel/Elektro aus dem Roh-Typ.
- ``model.country``: ``DR`` + Epoche ``IV`` und DDR-Kontext, aber ``DE`` → ``DD``.

Usage::

    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_trix_shop_import.py articles/trix
    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_trix_shop_import.py --apply articles/trix
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

Article = dict[str, Any]

_PRODUCT_PREFIX = re.compile(
    r"^(?:Schlepptender-)?(?:Dampf|Diesel|Elektro|Zweikraft)lokomotive\s+",
    re.I,
)
_BAUREIHE = re.compile(r"^Baureihe\s+(.+)$", re.I)
_REIHE = re.compile(r"^Reihe\s+(.+)$", re.I)
_TYP = re.compile(r"^Typ\s+(.+)$", re.I)
_QUOTE = re.compile(r'[„"\']([^"\']+)[„"\']')
_BETRIEBSNR = re.compile(
    r"(?:Lok-)?Betriebsnummer\s*[:=]?\s*"
    r"(?P<num>"
    r"E?\s*\d+(?:\.\d+)?(?:\s+\d+(?:-\d+)?)?"  # 218 140-2, E 94 026, 01 1059
    r"|\d{3,5}(?:-\d)?"  # 1210, 8099
    r")",
    re.I,
)


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


def _is_trix(article: Article) -> bool:
    if (article.get("manufacturer") or "").strip().lower() == "trix":
        return True
    url = ((article.get("source") or {}).get("url") or "").lower()
    return "trix.de" in url


def _vorbild(desc: str) -> str:
    if not desc:
        return ""
    return desc.split("Modell:", 1)[0]


def _normalize_type(raw: str) -> tuple[str, Optional[str]]:
    """Return (new_type, quoted_name_for_livery)."""
    t = re.sub(r"\s+", " ", raw.strip())
    quoted: Optional[str] = None
    qm = _QUOTE.search(t)
    if qm:
        quoted = qm.group(1).strip()
        t = (_QUOTE.sub("", t)).strip()
        t = re.sub(r"\s+", " ", t).strip(" ,;-")

    t = _PRODUCT_PREFIX.sub("", t).strip()

    # «1.002» allein nach Strip von «Dampflokomotive 1.002» → Reihe 1
    if re.fullmatch(r"\d+\.\d+", t):
        return f"Reihe {t.split('.', 1)[0]}", quoted

    m = _BAUREIHE.match(t)
    if m:
        rest = m.group(1).strip()
        # drop trailing variant words that are not the class id
        rest = re.sub(r"\s+Neubau$", "", rest, flags=re.I).strip()
        # Spitzname ohne Anführungszeichen am Ende (z. B. «477.0 Papagei»)
        nick = re.match(r"^(\d+(?:\.\d+)?)\s+([A-Za-zÄÖÜäöü][\w\-]*)$", rest)
        if nick and not quoted:
            quoted = nick.group(2)
            rest = nick.group(1)
        return f"BR {rest}", quoted

    m = _REIHE.match(t)
    if m:
        rest = m.group(1).strip()
        # NL-Konvention im Repo oft Rh
        if re.fullmatch(r"\d+", rest):
            return f"Rh {rest}", quoted
        return f"Reihe {rest}", quoted

    m = _TYP.match(t)
    if m:
        return m.group(1).strip(), quoted

    return t, quoted


def _number_from_description(desc: str, series_hint: str) -> Optional[str]:
    m = _BETRIEBSNR.search(_vorbild(desc))
    if not m:
        # Dampf «06 002» ohne Label
        m2 = re.search(
            r"\b(\d{2})\s+(\d{3,4})\b",
            _vorbild(desc),
        )
        if m2 and series_hint.rstrip(".").endswith(m2.group(1)):
            return m2.group(2)
        return None
    raw = re.sub(r"\s+", " ", m.group("num").strip())
    raw = raw.rstrip(".,;")
    # «218 140-2» → «140-2»; «E 94 026» → «026»; «01 1059» → «1059»
    parts = raw.split()
    if len(parts) >= 2 and re.match(r"^(?:E\s*)?\d", parts[0], re.I):
        return parts[-1]
    if raw.upper().startswith("E ") and len(parts) >= 3:
        return parts[-1]
    return raw

def _categories_for(raw_type: str, cats: list[str]) -> list[str]:
    out = list(cats) if cats else []
    if "lokomotive" not in out:
        out.insert(0, "lokomotive")
    low = raw_type.lower()
    add: Optional[str] = None
    if "dampf" in low:
        add = "dampflokomotive"
    elif "diesel" in low or "zweikraft" in low:
        add = "diesellokomotive"
    elif "elektro" in low or low.startswith("ae "):
        add = "elektrolokomotive"
    if add and add not in out:
        out.append(add)
    return out


def propose(article: Article) -> Optional[dict[str, Any]]:
    if not _is_trix(article):
        return None
    model = article.get("model") or {}
    raw_type = model.get("type")
    if not isinstance(raw_type, str) or not raw_type.strip():
        return None

    changes: dict[str, Any] = {}
    new_type, quoted = _normalize_type(raw_type)
    if new_type != raw_type.strip():
        changes["type"] = new_type

    num = model.get("number")
    if num is None or (isinstance(num, str) and not num.strip()):
        extracted = _number_from_description(
            article.get("description") or "",
            series_hint=new_type,
        )
        if extracted:
            changes["number"] = extracted

    liv = model.get("livery")
    if quoted and (liv is None or (isinstance(liv, str) and not liv.strip())):
        changes["livery"] = quoted

    cats = article.get("categories") if isinstance(article.get("categories"), list) else []
    new_cats = _categories_for(raw_type, [str(c) for c in cats])
    if new_cats != list(cats):
        changes["categories"] = new_cats

    op = (model.get("operator") or "").strip()
    era = (model.get("era") or "").strip()
    country = (model.get("country") or "").strip()
    blob = f"{article.get('description') or ''} {raw_type}"
    if op == "DR" and era == "IV" and country == "DE" and re.search(r"\bDDR\b|Reichsbahn", blob, re.I):
        changes["country"] = "DD"
    if op == "DR" and era == "III" and country == "DE" and re.search(r"DR/DDR|Reichsbahn der DDR", blob, re.I):
        changes["country"] = "DD"

    if not changes:
        return None
    return changes


def apply_changes(article: Article, changes: dict[str, Any]) -> Article:
    model = dict(article.get("model") or {})
    for key in ("type", "number", "livery", "country"):
        if key in changes:
            model[key] = changes[key]
    article = dict(article)
    article["model"] = model
    if "categories" in changes:
        article["categories"] = changes["categories"]
    return article


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    files = _walk(args.paths)
    n = 0
    for path in files:
        art = json.loads(path.read_text(encoding="utf-8"))
        ch = propose(art)
        if not ch:
            continue
        n += 1
        bits = ", ".join(f"{k}={v!r}" for k, v in ch.items())
        print(f"{path}: {bits}")
        if args.apply:
            new_art = apply_changes(art, ch)
            path.write_text(
                json.dumps(new_art, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    print(f"{'Updated' if args.apply else 'Would update'} {n} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
