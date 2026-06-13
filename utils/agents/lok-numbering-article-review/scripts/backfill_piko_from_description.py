#!/usr/bin/env python3
"""
Backfill PIKO article fields from embedded ``description`` text (Shop-Attributblock).

Fills when leer bzw. Shop-Platzhalter, konservativ:

- ``model.era`` aus ``Epoche:``
- ``model.operator`` aus ``Bahnverwaltung:`` (nicht «Privatbahn» überschreiben, wenn Modell schon EVU)
- ``model.country`` aus Operator-Map (Parser-Logik)
- ``model.number`` aus erster Titelzeile (UIC / Betriebsnummer)
- ``model.livery`` aus erster Titelzeile (Sonderlack, nicht Staatsbahn allein)
- ``model.electricSystem`` aus ``Stromsystem:`` + Sound-Hinweis (Parser-Logik)

Usage::

    python3 utils/agents/lok-numbering-article-review/scripts/backfill_piko_from_description.py articles/piko
    python3 utils/agents/lok-numbering-article-review/scripts/backfill_piko_from_description.py --apply articles/piko
    python3 ... --tag piko-neuheiten-2023 --apply articles/piko
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_REPO = Path(__file__).resolve().parents[4]
_PARSER = _REPO / "utils" / "piko" / "shop-pdp-parse" / "piko_shop_parse_pdp.py"

_ROMAN_ERA = re.compile(r"\b(I{1,3}|IV|V|VI|III-IV|II-III|IV-V|V-VI)\b", re.I)
_STATE_OPS = frozenset(
    {
        "DB",
        "DB AG",
        "DR",
        "DRG",
        "PKP",
        "PKP Cargo",
        "ÖBB",
        "OBB",
        "SBB",
        "SBB Cargo",
        "BLS",
        "BLS Cargo",
        "CD",
        "ČSD",
        "CSD",
        "NS",
        "MAV",
        "FS",
        "SNCF",
        "ZSSK",
        "VSM",
        "CFL",
        "DSB",
    }
)


def _load_parser():
    spec = importlib.util.spec_from_file_location("piko_shop_parse_pdp", _PARSER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load parser: {_PARSER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _walk(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = raw if raw.is_absolute() else Path.cwd() / raw
        if p.is_file() and p.suffix == ".json":
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(p.rglob("*.json")))
    return out


def _parse_description_attrs(description: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (description or "").splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if key and val:
            out[key] = val
    return out


def _first_title_line(description: str) -> str:
    first = (description or "").split("\n", 1)[0]
    return re.split(r"\s+Modelleisenbahn", first, flags=re.I)[0].strip()


def _strip_title_noise(s: str) -> str:
    u = s
    for _ in range(8):
        old = u
        u = re.sub(
            r"^(?:Sound[- ]?)?(?:Zweikraftlok|Elektotriebwagen|Elektrotriebwagen|Elektrotriebzug|"
            r"Dieseltriebwagen|Elektrolokomotive|Diesellokomotive|Schlepptenderlok|Dampflok|"
            r"Elektrolok|Diesellok|E[- ]?Triebzug|E-Triebzug|Sound-E-Triebzug|E[- ]?Lok|"
            r"E[- ]?Triebwagen|Zugset|Start-Set)\s+",
            "",
            u,
            count=1,
            flags=re.I,
        )
        u = re.sub(r"^Diesellok/Sound\s+", "", u, count=1, flags=re.I)
        if u == old:
            break
    u = re.sub(r",?\s*inkl\.\s*PIKO Sound-Decoder.*$", "", u, flags=re.I)
    u = re.sub(r"\s+Wechselstromversion.*$", "", u, flags=re.I)
    u = re.sub(r"\s+und Dampfgenerator.*$", "", u, flags=re.I)
    return u.strip()


def _propose_number(first: str, model_type: str) -> Optional[str]:
    typ = (model_type or "").strip()
    if not typ:
        return None

    m_br = re.search(r"BR\s+(\d+(?:\.\d+)?)", typ, re.I)
    if m_br:
        br = m_br.group(1).replace(".", r"\.")
        m = re.search(rf"\b{br}\s+(\d{{2,4}})\b", first.replace(".", ""))
        if m:
            return m.group(1)

    m_pair = re.search(
        r"(?:E-Lok|Sound-E-Lok|Elektrolok|Sound-Elektrolok)\s+(\d{3})\s+(\d{2,4})",
        first,
        re.I,
    )
    if m_pair:
        br_digit = m_br.group(1).split(".")[0] if m_br else m_pair.group(1)
        if m_br and m_pair.group(1) == br_digit:
            return m_pair.group(2)
        if not m_br and typ.strip() == m_pair.group(1):
            return m_pair.group(2)

    m_e32 = re.search(r"\bE\s+32\s+(\d+)\b", first, re.I)
    if m_e32 and re.search(r"E\s*32", typ, re.I):
        return m_e32.group(1)

    m_v43 = re.search(r"V\s+43\s+Jubil", first, re.I)
    if m_v43 and re.search(r"V\s*43", typ, re.I):
        m_num = re.search(r"Jubil[aä]umslok\s+(\d+)", first, re.I)
        if m_num:
            return m_num.group(1)

    m_rh = re.search(r"\bRh\s+([\d.]+)", first, re.I)
    if m_rh and re.fullmatch(r"Rh", typ, re.I):
        return m_rh.group(1).replace(".", "")

    return None


def _propose_livery(
    first: str,
    model_type: str,
    operator: Optional[str],
    proposed_number: Optional[str],
) -> Optional[str]:
    typ = (model_type or "").strip()
    first_low = first.lower()
    for phrase in ("DB Cargo Polska", "PKP Cargo", "SBB Cargo International", "DB Italia"):
        if phrase.lower() in first_low and phrase.lower() not in typ.lower():
            return phrase

    s = _strip_title_noise(first)
    if typ:
        s = re.sub(re.escape(typ), "", s, count=1, flags=re.I).strip()
        m_br = re.match(r"BR\s+(.+)", typ, re.I)
        if m_br:
            s = re.sub(rf"\bBR\s+{re.escape(m_br.group(1))}\b", "", s, flags=re.I).strip()
        m_et = re.match(r"ET\s+(\d+)", typ, re.I)
        if m_et:
            s = re.sub(rf"\bET\s+{re.escape(m_et.group(1))}\b", "", s, flags=re.I).strip()

    if operator:
        s = re.sub(rf"\b{re.escape(operator)}\b", "", s, flags=re.I).strip()
    for op in _STATE_OPS:
        s = re.sub(rf"\b{re.escape(op)}\b", "", s, flags=re.I).strip()
    s = _ROMAN_ERA.sub("", s).strip()
    s = re.sub(r"\s+", " ", s).strip(" ,-")
    if not s or len(s) < 2 or len(s) > 48:
        return None
  # Kein UIC-Rest, keine Klassenziffer, kein Operator-Splitter
    if re.fullmatch(r"\d+", s):
        return None
    if re.fullmatch(r"\d{3}\s+\d{2,4}", s):
        return None
    if proposed_number and s.replace(" ", "") == str(proposed_number).replace(" ", ""):
        return None
    if re.fullmatch(r"Rh", typ, re.I) and re.fullmatch(r"[\d.]+", s):
        return None
    low = s.lower()
    if low in ("sound", "diesellok", "elektrolok", "dampflok", "e-lok", "vectron", "ag", "cargo"):
        return None
    if low in {x.lower() for x in _STATE_OPS}:
        return None
    if re.match(r"^(sound-)?schienenbus\b", low):
        return None
    return s


def _country_missing(model: dict[str, Any]) -> bool:
    c = model.get("country")
    return c is None or (isinstance(c, str) and not c.strip())


def _apply_backfill(article: dict[str, Any], parser: Any) -> list[str]:
    changes: list[str] = []
    desc = article.get("description") or ""
    if not desc.strip():
        return changes
    model = article.get("model")
    if not isinstance(model, dict):
        return changes

    attrs = _parse_description_attrs(desc)
    first = _first_title_line(desc)

    era_raw = attrs.get("Epoche", "").strip()
    if era_raw and (
        model.get("era") is None
        or (isinstance(model.get("era"), str) and not str(model.get("era")).strip())
    ):
        if model.get("era") != era_raw:
            changes.append(f"era: {model.get('era')!r} -> {era_raw!r}")
            model["era"] = era_raw

    desc_op_raw = attrs.get("Bahnverwaltung", "").strip()
    desc_op = parser._normalize_piko_operator(desc_op_raw) if desc_op_raw else ""
    cur_op = model.get("operator")
    cur_op_s = cur_op.strip() if isinstance(cur_op, str) else ""
    if desc_op and desc_op != "Privatbahn":
        if not cur_op_s or cur_op_s == "Privatbahn":
            if cur_op != desc_op:
                changes.append(f"operator: {cur_op!r} -> {desc_op!r}")
                model["operator"] = desc_op
    elif desc_op and not cur_op_s:
        changes.append(f"operator: {cur_op!r} -> {desc_op!r}")
        model["operator"] = desc_op

    era_for_country = model.get("era")
    op_for_country = model.get("operator")
    if isinstance(op_for_country, str) and op_for_country.strip() and _country_missing(model):
        mapped = parser._operator_to_country(
            parser._normalize_piko_operator(op_for_country), era_for_country
        )
        if mapped:
            changes.append(f"country: {model.get('country')!r} -> {mapped!r}")
            model["country"] = mapped

    if model.get("number") is None or (
        isinstance(model.get("number"), str) and not str(model.get("number")).strip()
    ):
        prop_n = _propose_number(first, str(model.get("type") or ""))
        if prop_n:
            changes.append(f"number: {model.get('number')!r} -> {prop_n!r}")
            model["number"] = prop_n
    else:
        prop_n = str(model.get("number") or "").strip() or None

    if model.get("livery") is None or (
        isinstance(model.get("livery"), str) and not str(model.get("livery")).strip()
    ):
        prop_l = _propose_livery(
            first,
            str(model.get("type") or ""),
            model.get("operator") if isinstance(model.get("operator"), str) else None,
            prop_n if prop_n else _propose_number(first, str(model.get("type") or "")),
        )
        if prop_l:
            changes.append(f"livery: {model.get('livery')!r} -> {prop_l!r}")
            model["livery"] = prop_l

    es = parser._canonical_electric_system_from_description(desc)
    if es and model.get("electricSystem") != es:
        # nur wenn Beschreibung eindeutig (Stromsystem-Zeile)
        if "Stromsystem:" in desc:
            changes.append(f"electricSystem: {model.get('electricSystem')!r} -> {es!r}")
            model["electricSystem"] = es

    return changes


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path, default=[Path("articles/piko")])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--tag", metavar="SLUG", default=None, help="Nur Artikel mit diesem Tag.")
    args = ap.parse_args(argv)
    parser = _load_parser()
    files = _walk([p.expanduser().resolve() for p in args.paths])
    updated = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: {path}: {e}", file=sys.stderr)
            return 1
        if args.tag:
            tags = data.get("tags") or []
            if args.tag not in tags:
                continue
        changes = _apply_backfill(data, parser)
        if not changes:
            continue
        print(f"{path}")
        for c in changes:
            print(f"  {c}")
        if args.apply:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            updated += 1
    if args.apply:
        print(f"\nUpdated {updated} file(s).", file=sys.stderr)
    elif any(True for _ in files):
        print("\nDry-run: re-run with --apply to write.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
