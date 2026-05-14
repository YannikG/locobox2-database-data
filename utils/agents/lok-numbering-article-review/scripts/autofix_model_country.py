#!/usr/bin/env python3
"""
Autofix: set ``model.country`` when it is null and the case matches a **conservative** allowlist.

Tier **A** — ``SKILL.md`` «Allowlist: model.country»::

  - ``operator`` «K.P.E.V.» → ``DE``
  - ``operator`` «Südbahn» (inkl. OCR «Sudbahn») + AT-Kontext in ``description``/``categories`` → ``AT``

Tier **B** — explizite Operator→ISO-Zuordnung für klar staatliche oder eindeutig nationale Systeme
(siehe ``_OPERATOR_COUNTRY``): u. a. **DB** → ``DE``, **CSD** → ``CS`` (wie bestehende ČSD-Artikel),
**VSM** → ``NL``, **GTS Rail** → ``IT``, **SBW** (Starkenberger Güterlogistik) → ``AT``.

**DR** (Deutsche Reichsbahn): ``IV`` in ``model.era`` → ``DD``; reine Epochen **I**–**III**
(ohne ``IV``) → ``DE``; **fehlende** Epoche oder andere Schreibweisen (z. B. **V**, **VI**) →
``DD`` (Roco-Importe: DDR-Reichsbahn als Default, wenn nicht eindeutig DRG-Frühzeit).

Usage::

    python3 utils/agents/lok-numbering-article-review/scripts/autofix_model_country.py articles/roco/70073.json
    python3 utils/agents/lok-numbering-article-review/scripts/autofix_model_country.py --apply articles/roco
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Optional


Article = dict[str, Any]


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


def load_article(path: Path) -> Article:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_article(path: Path, data: Article) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _country_missing(model: dict[str, Any]) -> bool:
    c = model.get("country")
    if c is None:
        return True
    if isinstance(c, str) and not c.strip():
        return True
    return False


def _norm_op(raw: Any) -> str:
    if not isinstance(raw, str):
        return ""
    return unicodedata.normalize("NFKC", raw).strip()


def _text_blob(article: Article) -> str:
    parts: list[str] = []
    d = article.get("description")
    if isinstance(d, str):
        parts.append(d)
    cats = article.get("categories")
    if isinstance(cats, list):
        parts.extend(str(x) for x in cats if x is not None)
    return " ".join(parts)


_DR_ERA_DE = re.compile(r"^(I|II|III)(-(I|II|III))*$", re.I)


def _dr_rule_and_country(era_raw: Any) -> tuple[str, str]:
    """``operator`` «DR»: Regel-ID und ISO-Land."""
    if not isinstance(era_raw, str):
        return ("dr_era_default", "DD")
    eu = era_raw.strip().upper().replace(" ", "")
    if not eu:
        return ("dr_era_default", "DD")
    if "IV" in eu:
        return ("dr_era_contains_iv", "DD")
    if _DR_ERA_DE.fullmatch(eu):
        return ("dr_era_reichsbahn_i_iii", "DE")
    return ("dr_era_default", "DD")


def _suedbahn_at_context(blob: str) -> bool:
    """AT-Kontext wie in SKILL.md (k. k. Südbahn, Österreich, …)."""
    low = blob.lower()
    if "österreich" in low or "osterreich" in low:
        return True
    if "österreichisch" in low or "osterreichisch" in low:
        return True
    if re.search(r"\bwien\b", low):
        return True
    if "triest" in low or "trieste" in low:
        return True
    if "k.k." in blob or "k. k." in blob:
        return True
    if "kkstb" in low or "kköst" in low:
        return True
    if "öbb" in low or "oebb" in low:
        return True
    return False


# Tier B: exakter Operator-String nach Import/Parser (kein Regex auf Teilstrings).
# Nur eindeutig national/staatlich zugeordnete Operatoren oder von SKILL.md namentlich
# erlaubte Sonderfälle. Nicht aufnehmen: Vermietung (MRCE, Railpool, LTE), reine
# Grenzverkehr-Operator-Strings (TX Logistik), Mischungen (z. B. SNCB/SŽ-Mischfälle).
_OPERATOR_COUNTRY: dict[str, str] = {
    "ÖBB": "AT",
    "SBB Cargo": "CH",
    "PKP": "PL",
    "PKP Cargo": "PL",
    "MAV": "HU",
    "SNCF": "FR",
    "CD": "CZ",
    "ZSSK": "SK",
    "K.W.St.E.": "DE",
    "DB": "DE",
    "CSD": "CS",
    "VSM": "NL",
    "NS": "NL",
    "GTS Rail": "IT",
    "Mercitalia Rail": "IT",
    "SBW": "AT",
    "BLS Cargo": "CH",
    "DRG": "DE",
    "SNCB": "BE",
}


def propose_country(article: Article) -> Optional[tuple[str, str]]:
    """
    Returns (rule_id, iso_country) or None.
    """
    model = article.get("model")
    if not isinstance(model, dict) or not _country_missing(model):
        return None

    op = _norm_op(model.get("operator"))
    if not op:
        return None

    if op == "K.P.E.V.":
        return ("skill_kpev", "DE")

    if op in ("Südbahn", "Sudbahn"):
        if _suedbahn_at_context(_text_blob(article)):
            return ("skill_suedbahn_at", "AT")
        return None

    if op == "DR":
        rule_id, iso = _dr_rule_and_country(model.get("era"))
        return (rule_id, iso)

    if op in _OPERATOR_COUNTRY:
        return (f"operator_map:{op}", _OPERATOR_COUNTRY[op])

    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("articles")],
        help="Article JSON files or directories",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write updated JSON (default is dry-run)",
    )
    args = ap.parse_args(argv)
    dry_run = not args.apply

    files = _walk([p.expanduser().resolve() for p in args.paths])
    changed: list[tuple[Path, str, str]] = []

    for path in files:
        try:
            data = load_article(path)
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: {path}: {e}", file=sys.stderr)
            return 1
        model = data.get("model")
        if not isinstance(model, dict):
            continue
        prop = propose_country(data)
        if not prop:
            continue
        rule_id, new_c = prop
        old_c = model.get("country")
        if old_c == new_c:
            continue
        changed.append((path, rule_id, new_c))
        if not dry_run:
            model["country"] = new_c
            save_article(path, data)

    for path, rule_id, new_c in changed:
        print(f"{path}\t{rule_id}\tcountry -> {new_c!r}")

    if dry_run and changed:
        print(f"\n{len(changed)} file(s) would change; re-run with --apply.", file=sys.stderr)
    elif dry_run:
        print("No changes.", file=sys.stderr)
    else:
        print(f"Updated {len(changed)} file(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
