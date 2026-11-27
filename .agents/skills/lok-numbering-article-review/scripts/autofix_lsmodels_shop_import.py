#!/usr/bin/env python3
"""
Autofix LS Models Shop-Importreste (Allowlist, konservativ).

- Langer PrestaShop-H1 in ``model.type`` → Split via ``split_lsmodels_title``
  (HLE, BB/CC, X####, AGC/Z, Vectron, Apm/Bpm, …).
- ``operator``/``country``: PAYS-/Titel-Heuristik (SNCF→FR, SNCB/LINEAS→BE, …).
- Kategorien: Autorail/AGC → Triebwagen; Apm/Bpm/I*/M6/OCEM → Wagen;
  HLE/BB/CC/Vectron → Elektro-Lok.

Usage::

    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_lsmodels_shop_import.py articles/lsmodels
    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_lsmodels_shop_import.py --apply articles/lsmodels
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

Article = dict[str, Any]

_CLI_SRC = Path(__file__).resolve().parents[4] / "tools" / "cli" / "src"
if _CLI_SRC.is_dir():
    sys.path.insert(0, str(_CLI_SRC))

try:
    from locobox_cli.adapters.sources.lsmodels.parse_pdp import (  # type: ignore
        split_lsmodels_title,
        _operator_from_title,
        _categories_from_materiel,
    )
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "error: locobox_cli not importable; run from repo with tools/cli present"
    ) from exc


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


def _is_lsmodels(article: Article) -> bool:
    mfr = (article.get("manufacturer") or "").strip().lower()
    if mfr in {"l.s.models", "lsmodels", "ls models", "l.s. models"}:
        return True
    url = ((article.get("source") or {}).get("url") or "").lower()
    return "lsmodels.eu" in url or "lsmodels.com" in url


def _needs_title_split(typ: str, number: Any) -> bool:
    t = (typ or "").strip()
    if not t or t == "Unbekannt":
        return False
    if "," in t and len(t) > 28:
        return True
    if number in (None, "", "Unbekannt") and re.match(
        r"^(?:BB|CC|HLE|X\s*\d|Z\s+\d|Apm|Bpm|Vectron|BR\s*\d|\d{3,5}\s*[, ])",
        t,
        re.I,
    ):
        return True
    return False


def propose_fixes(article: Article) -> list[tuple[str, str, Any]]:
    """Return list of (rule, dotted_path, new_value)."""
    if not _is_lsmodels(article):
        return []
    model = article.get("model")
    if not isinstance(model, dict):
        return []

    changes: list[tuple[str, str, Any]] = []
    typ = model.get("type") if isinstance(model.get("type"), str) else ""
    number = model.get("number")
    desc = article.get("description") if isinstance(article.get("description"), str) else ""
    # Only re-split when *type* still looks like a raw H1. Never expand an already
    # short type back from description (that undoes prior autofix).
    source = typ if _needs_title_split(typ, number) else ""

    if source:
        nt, nn, liv = split_lsmodels_title(source, categorie="")
        # Prefer shorter cleaned type; never replace a short type with a longer dump.
        if nt and nt != typ and not (len(nt) > len(typ) and "," not in typ and "," in nt):
            changes.append(("ls_title_split:type", "model.type", nt))
            typ = nt
        if nn != number and (nn is not None or number not in (None, "")):
            # only set number when we found one, or clear bogus duplicate of type
            if nn is not None or (isinstance(number, str) and number.strip() == typ.strip()):
                changes.append(("ls_title_split:number", "model.number", nn))
        cur_liv = model.get("livery")
        if liv and liv != cur_liv and (
            cur_liv in (None, "", "Unbekannt")
            or (isinstance(cur_liv, str) and len(cur_liv) > 60)
        ):
            changes.append(("ls_title_split:livery", "model.livery", liv))

    # Operator / country
    op = model.get("operator") if isinstance(model.get("operator"), str) else "Unbekannt"
    country = model.get("country")
    blob = f"{typ} {desc} {source}"
    new_op, new_cc = _operator_from_title(blob, "")
    if op in ("Unbekannt", "", None) and new_op != "Unbekannt":
        changes.append(("ls_operator_title", "model.operator", new_op))
        op = new_op
        if country in (None, "", "Unbekannt") or (country == "DE" and new_cc != "DE"):
            changes.append(("ls_operator_title:country", "model.country", new_cc))
            country = new_cc
    if op in ("Unbekannt", "", None) and re.match(
        r"^(?:BB|CC)\s+\d|^X\s+\d{3,4}\b|^AGC\b",
        typ or "",
        re.I,
    ):
        changes.append(("ls_sncf_bbcc_op", "model.operator", "SNCF"))
        changes.append(("ls_sncf_bbcc_country", "model.country", "FR"))
        op, country = "SNCF", "FR"
    if op in ("Unbekannt", "", None) and re.match(r"^HLE\s+\d", typ or "", re.I):
        if re.search(r"\bLINEAS\b", blob, re.I):
            changes.append(("ls_hle_lineas", "model.operator", "LINEAS"))
            changes.append(("ls_hle_lineas:country", "model.country", "BE"))
        elif re.search(r"\b(?:SNCB|NMBS)\b", blob, re.I):
            changes.append(("ls_hle_sncb", "model.operator", "SNCB"))
            changes.append(("ls_hle_sncb:country", "model.country", "BE"))

    # Categories
    cats = article.get("categories")
    if not isinstance(cats, list):
        cats = []
    # Ergänzungswagen / Grossraumwagen in Triebzug-Sets → wagen (not Triebwagen)
    if re.search(
        r"(?i)^(?:Grossraumwagen|Speisewagen|Erg(?:ä|ae)nzungswagen)\b", typ or ""
    ):
        if cats != ["wagen"]:
            changes.append(("ls_coach_cat", "categories", ["wagen"]))
    # Pantographen-Sets sind Zubehör (kein Rollmaterial): Parser importiert sie nicht,
    # Kategorien hier nicht anfassen.
    if re.search(r"(?i)fahrstromabnehmer|pantographe", typ or ""):
        pass
    else:
        want = _categories_from_materiel("", categorie="", title=f"{typ} {desc}")
        # Only replace when clearly wrong (lokomotive-only on coach/triebwagen, or empty)
        wrong_loco = (
            "lokomotive" in cats
            and "wagen" in want
            and not any(
                c.startswith("elektro") or c.startswith("diesel")
                for c in want
                if c != "lokomotive"
            )
        )
        wrong_trieb = "lokomotive" in cats and any(
            c in want for c in ("triebwagen", "elektrotriebwagen", "dieseltriebwagen")
        )
        if (not cats or wrong_loco or wrong_trieb) and want and want != cats:
            # Prefer want when title clearly classifies
            if re.search(
                r"(?i)\b(?:Apm|Bpm|I10|I2|M6|OCEM|AGC|X\s*\d|Vectron|HLE|BB|CC)\b",
                typ or "",
            ):
                changes.append(("ls_categories", "categories", want))

    return changes


def propose_ac_twin_fix(
    article: Article, by_num: dict[str, Article]
) -> list[tuple[str, str, Any]]:
    """AC twin = articleNumber base+500. Only when ALIMENTATION absent (DC default wrong)."""
    if not _is_lsmodels(article):
        return []
    model = article.get("model")
    if not isinstance(model, dict):
        return []
    art = str(article.get("articleNumber") or "").strip()
    if not art.isdigit():
        return []
    n = int(art)
    if n < 500:
        return []
    base = str(n - 500)
    if base not in by_num:
        return []
    cur = model.get("electricSystem")
    if cur not in (None, "Unbekannt", "DC-Analog", "DC-Digital"):
        return []
    # Already correctly AC
    if isinstance(cur, str) and cur.startswith("AC"):
        return []
    base_m = by_num[base].get("model") or {}
    base_e = base_m.get("electricSystem") if isinstance(base_m, dict) else None
    # Base should look DC (or unknown); twin must not already be marked AC
    if isinstance(base_e, str) and base_e.startswith("AC"):
        return []
    # Same type family (avoid accidental +500 collisions)
    t1 = (model.get("type") or "").strip()
    t2 = (base_m.get("type") or "").strip() if isinstance(base_m, dict) else ""
    if t1 and t2 and t1 != t2:
        return []
    return [("ls_ac_twin_plus500", "model.electricSystem", "AC-Digital")]


def _set_path(article: Article, dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur: Any = article
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    files = _walk(args.paths)
    if not files:
        print("error: no json files", file=sys.stderr)
        return 2

    loaded: list[tuple[Path, Article]] = []
    by_num: dict[str, Article] = {}
    for path in files:
        try:
            article = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            continue
        if not isinstance(article, dict) or not _is_lsmodels(article):
            continue
        loaded.append((path, article))
        art = str(article.get("articleNumber") or "").strip()
        if art:
            by_num[art] = article

    n_files = 0
    for path, article in loaded:
        fixes = propose_fixes(article) + propose_ac_twin_fix(article, by_num)
        if not fixes:
            continue
        n_files += 1
        for rule, dotted, value in fixes:
            old: Any = article
            for part in dotted.split(".")[:-1]:
                old = old.get(part, {}) if isinstance(old, dict) else {}
            old_v = old.get(dotted.split(".")[-1]) if isinstance(old, dict) else None
            print(f"{path}: {rule} {dotted}: {old_v!r} → {value!r}")
            if args.apply:
                _set_path(article, dotted, value)
        if args.apply:
            path.write_text(
                json.dumps(article, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    print(f"{'applied' if args.apply else 'dry-run'}: {n_files} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
