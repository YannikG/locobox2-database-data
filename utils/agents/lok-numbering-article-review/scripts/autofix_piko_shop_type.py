#!/usr/bin/env python3
"""
PIKO-Shop: ``model.type`` bereinigen (Sound-/Marketing-Reste) und splitten.

Nur ``articles/piko`` bzw. PIKO-Artikel (``manufacturer`` / ``piko-shop.de``-URL).
Setzt bei Bedarf ``model.number`` und ``model.livery`` (nur wenn ``livery`` noch ``null``).

Usage::

    python3 utils/agents/lok-numbering-article-review/scripts/autofix_piko_shop_type.py articles/piko
    python3 utils/agents/lok-numbering-article-review/scripts/autofix_piko_shop_type.py --apply articles/piko
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

Article = dict[str, Any]
Fix = tuple[str, str, Optional[str], Optional[str]]  # rule, type, number, livery

_ROMAN = r"(?:I{1,3}|IV|V|VI|III-IV|II-III|IV-V|V-VI)"
_ROMAN_RE = re.compile(rf"\b{_ROMAN}\b", re.I)


def _is_piko(article: Article) -> bool:
    if (article.get("manufacturer") or "").strip().upper() == "PIKO":
        return True
    return "piko-shop.de" in ((article.get("source") or {}).get("url") or "").lower()


def _strip_prefix(t: str) -> str:
    u = t.strip()
    u = re.sub(r"^[~]\s*", "", u)
    for _ in range(6):
        old = u
        u = re.sub(r"^Sound[- ]?", "", u, count=1, flags=re.I)
        u = re.sub(
            r"^(Zweikraftlok|Elektrotriebwagen|Dieseltriebwagen|Elektrolokomotive|"
            r"Diesellokomotive|Schlepptenderlok|Dampflok|Elektrolok|Diesellok|"
            r"E[- ]?Triebzug|E-Triebzug|Sound-E-Triebzug|E-Lok|Zugset)\s+",
            "",
            u,
            count=1,
            flags=re.I,
        )
        u = re.sub(r"^Diesellok/Sound\s+", "", u, count=1, flags=re.I)
        u = u.strip()
        if u == old:
            break
    return u


def _strip_suffixes(u: str, article: Article) -> str:
    model = article.get("model") or {}
    era = (model.get("era") or "").strip()
    u = re.sub(r",?\s*inkl\.?\s*PIKO Sound-Decoder.*$", "", u, flags=re.I)
    u = re.sub(r"\s+und Dampfgenerator.*$", "", u, flags=re.I)
    u = re.sub(r"\s+Wechselstromversion.*$", "", u, flags=re.I)
    u = re.sub(r"\s+modifiziert.*$", "", u, flags=re.I)
    u = re.sub(r"\s+DB AG\s+[IVX]+\s+Wechselstrom\s*$", "", u, flags=re.I)
    if era:
        u = re.sub(rf"\s+{re.escape(era)}\s*$", "", u, flags=re.I)
    u = re.sub(rf"\s+{_ROMAN}\s*$", "", u, flags=re.I)
    u = re.sub(
        r",?\s+(?:DB(?:\s+AG)?|DR(?:G)?|PKP(?:\s+Cargo)?|ÖBB|OBB|CD|ČSD|CSD|FS|SNCF|NS|DSB|MAV|"
        r"SBB(?:\s+Cargo(?:\s+International)?)?|WFL|Medway|D&RGW|SP)\s*$",
        "",
        u,
        flags=re.I,
    )
    u = re.sub(r",\s*S-Bahn Leipzig$", "", u, flags=re.I)
    u = re.sub(r",\s*Messe Leipzig$", "", u, flags=re.I)
    u = re.sub(r"\s+SBB Cargo Int\.?\s*$", "", u, flags=re.I)
    return u.strip(" ,")


def _clean_type(raw: str, article: Article) -> str:
    u = _strip_suffixes(_strip_prefix(raw), article)
    u = re.sub(r"\bBR(\d{3})\b", r"BR \1", u, flags=re.I)
    u = re.sub(r"\bRh(\d{2,5})\b", r"Rh \1", u, flags=re.I)
    return re.sub(r"\s+", " ", u).strip()


def _livery_ok(current: Any) -> bool:
    return current is None or (isinstance(current, str) and not current.strip())


def _pick_livery(article: Article, candidate: Optional[str]) -> Optional[str]:
    if not candidate or not _livery_ok((article.get("model") or {}).get("livery")):
        return None
    c = candidate.strip(" ,")
    if not c or _ROMAN_RE.fullmatch(c):
        return None
    if len(c) > 48:
        return None
    return c


def propose_fix(article: Article) -> Optional[Fix]:
    if not _is_piko(article):
        return None
    model = article.get("model") or {}
    raw = model.get("type")
    if not isinstance(raw, str) or not raw.strip():
        return None
    n = model.get("number")
    if n is not None and isinstance(n, str) and n.strip():
        return None

    clean = _clean_type(raw, article)
    desc = (article.get("description") or "") + " " + ((article.get("source") or {}).get("url") or "")
    desc_l = desc.lower()

    # Vectron: «BR 7193» / «BR 3193» → Baureihe 193 + Betriebsnummer
    m = re.fullmatch(r"BR (\d{4})", clean, re.I)
    if m and ("vectron" in desc_l or "dual mode" in desc_l or "zweikraftlok" in desc_l):
        num = m.group(1)
        liv = None
        if "medway" in desc_l:
            liv = "Medway"
        elif "stern hafferl" in desc_l:
            liv = "Stern Hafferl"
        return ("piko_vectron", "BR 193", num, liv)

    # BR 243 / 143 WFL (vor generischem UIC-Split)
    m = re.match(r"^(\d{3}) (\d{2,3})\b", clean)
    if m and m.group(1) in ("143", "243") and "wfl" in desc_l:
        liv = _pick_livery(article, "S-Bahn Leipzig" if "s-bahn leipzig" in desc_l else None)
        return ("piko_br243", f"BR {m.group(1)}", m.group(2), liv)

    # Deutsche UIC ohne BR: «185 329 Black Dragons»
    m = re.fullmatch(r"(\d{3}) (\d{2,3})(?:\s+(.+))?", clean)
    if m and (model.get("country") or "") in ("DE", "AT", "CH", "DD"):
        liv = _pick_livery(article, m.group(3))
        return ("piko_uic_br", f"BR {m.group(1)}", m.group(2), liv)

    # BR 243 / 143-Stil: «243 019 WFL» — handled above

    # V 200: «V200 1001»
    m = re.fullmatch(r"V200 (\d{3,4})(?:\s+.*)?", clean, re.I)
    if m:
        liv = None
        if "messe leipzig" in desc_l or "messe leipzig" in raw.lower():
            liv = _pick_livery(article, "Messe Leipzig")
        return ("piko_v200", "V 200", m.group(1), liv)

    # Polnisch: «201E-277»
    m = re.fullmatch(r"([\dA-Z]+E)-(\d{2,3})(?:,.*)?", clean, re.I)
    if m:
        return ("piko_pl_e", m.group(1), m.group(2), None)

    # BR / Rh (inkl. langer Shop-Titel nach Clean)
    m = re.search(
        r"\b((?:BR|Rh)\s+\d+(?:\.\d+)?)(?:\s+(\d{2,4}))?(?=\s|$|[,\"\u201e\u201c(])",
        clean,
        re.I,
    )
    if m:
        series = re.sub(r"\s+", " ", m.group(1).strip())
        sub = m.group(2)
        tail = clean[m.end() :].strip()
        if series != raw.strip() or sub or tail:
            liv = _pick_livery(article, tail if not sub else None)
            return ("piko_br_rh", series, sub, liv)

    # NL/CH Diesellok «6400 Railion …»
    m = re.fullmatch(r"(\d{4})(?:\s+(.+))?", clean)
    if m and (model.get("country") or "") in ("NL", "BE", "LU"):
        liv = _pick_livery(article, m.group(2))
        return ("piko_nl_class", m.group(1), None, liv)

    # G 1206 / SM42 + Miet-Lackierer
    m = re.fullmatch(r"G (\d{4})(?:\s+(.+))?", clean, re.I)
    if m:
        liv = _pick_livery(article, m.group(2))
        return ("piko_g_class", f"G {m.group(1)}", None, liv)

    m = re.fullmatch(r"SM42(?:\s+(.+))?", clean, re.I)
    if m:
        liv = _pick_livery(article, m.group(1))
        return ("piko_sm42", "SM42", None, liv)

    # Nur bereinigen
    if clean != raw.strip():
        return ("piko_clean", clean, None, None)

    return None


def iter_files(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        p = root if root.is_absolute() else Path.cwd() / root
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(p.rglob("*.json")))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path, default=[Path("articles/piko")])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.apply and args.dry_run:
        print("error: --apply and --dry-run together", file=sys.stderr)
        return 2
    dry = not args.apply

    changed = 0
    for path in iter_files(list(args.paths)):
        data = json.loads(path.read_text(encoding="utf-8"))
        fix = propose_fix(data)
        if not fix:
            continue
        rule, new_t, new_n, new_liv = fix
        model = data["model"]
        old_t, old_n, old_liv = model.get("type"), model.get("number"), model.get("livery")
        if old_t == new_t and old_n == new_n and (new_liv is None or old_liv == new_liv):
            continue
        nn = "null" if new_n is None else repr(new_n)
        liv = "" if new_liv is None else f" livery={new_liv!r}"
        print(f"{path}\t{rule}\t{old_t!r}/{old_n!r} -> {new_t!r}/{nn}{liv}")
        if not dry:
            model["type"] = new_t
            model["number"] = new_n if new_n else None
            if new_liv and _livery_ok(old_liv):
                model["livery"] = new_liv
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed += 1

    print(f"\n{'Would update' if dry else 'Updated'} {changed} file(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
