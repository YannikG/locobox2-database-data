#!/usr/bin/env python3
"""
Autofix: set ``model.country`` when it is null and the case matches a **conservative** allowlist.

Tier **A** — ``SKILL.md`` «Allowlist: model.country»::

  - ``operator`` «K.P.E.V.» → ``DE``
  - ``operator`` «Südbahn» (inkl. OCR «Sudbahn») + AT-Kontext in ``description``/``categories`` → ``AT``

Tier **B** — explizite Operator→ISO-Zuordnung für klar staatliche oder eindeutig nationale Systeme
(siehe ``_OPERATOR_COUNTRY``): u. a. **DB** → ``DE``, **CSD** → ``CS`` (wie bestehende ČSD-Artikel),
**VSM** → ``NL``, **GTS Rail** → ``IT``, **SBW** (Starkenberger Güterlogistik) → ``AT``,
**D&RGW** / **SP (Southern Pacific)** → ``US`` (Nordamerika).

Tier **C** — **PIKO-Shop** ``operator`` «Privatbahn»: nur wenn ``model.type`` plus Fliesstext/
``categories`` eindeutige Marken- oder Bahngesellschaftsanker enthalten (siehe
``_privatbahn_infer_country``). Kein Blind-``DE`` für alle «Privatbahn»-Einträge.

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
from typing import Any, Callable, Optional


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
    s = unicodedata.normalize("NFKC", raw).strip()
    if s.lower() == "privatbahhn":
        return "Privatbahn"
    return s


def _text_blob(article: Article) -> str:
    parts: list[str] = []
    d = article.get("description")
    if isinstance(d, str):
        parts.append(d)
    model = article.get("model")
    if isinstance(model, dict):
        liv = model.get("livery")
        if isinstance(liv, str) and liv.strip():
            parts.append(liv)
        typ = model.get("type")
        if isinstance(typ, str) and typ.strip():
            parts.append(typ)
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
    "D&RGW": "US",
    "SP (Southern Pacific)": "US",
    "CFL": "LU",
    "USA": "US",
    "PR": "PL",
    "Norte": "US",
    "DB Cargo": "DE",
}


def _propose_missing_operator_fields(
    article: Article,
) -> Optional[tuple[str, Optional[str], Optional[str]]]:
    """
    Fehlender ``operator`` (und ggf. ``country``) aus Livery/Fliesstext — konservativ.
    Returns ``(rule_id, operator, country_or_none)``.
    """
    model = article.get("model")
    if not isinstance(model, dict):
        return None
    op = model.get("operator")
    if op is not None and isinstance(op, str) and op.strip():
        return None
    blob = _text_blob(article).lower()
    liv = str(model.get("livery") or "").lower()
    c = f"{liv} {blob}"
    if "db italia" in c or re.search(r"\b191 italia\b", c):
        return ("db_italia", "DB Italia", "IT")
    if "personenzug" in c and "db/dr" in c.replace(" ", ""):
        return ("personenzug_db_dr", "DB", "DE")
    if "piko jubil" in c:
        return ("piko_jubilaeum", None, "DE")
    if "slovakia" in liv or re.search(r"\bslovakia\b", c):
        return ("zssk_slovakia", "ZSSK", "SK")
    if re.search(r"\bt770\b", c) and re.search(r"\bcs\b", c):
        return ("cs_army_t770", "ČSD", "CS")
    if re.search(r"\bsu46\b", c) and "pkp" in c:
        return ("pkp_su46", "PKP", "PL")
    return None


def _privatbahn_infer_country(article: Article) -> Optional[tuple[str, str]]:
    """
    PIKO-Webshop setzt oft «Privatbahn» statt konkretem EVU. Nur bei klaren Textankern.
    Reihenfolge: spezifischere Teilstrings zuerst (z. B. «Railion Logistics NL» vor «Railion»).
    """
    model = article.get("model") or {}
    if not isinstance(model, dict):
        return None
    t = _norm_op(model.get("type"))
    liv = _norm_op(model.get("livery"))
    blob = _text_blob(article)
    c = f"{t} {liv} {blob}".lower()

    checks: list[tuple[str, str, Callable[[], bool]]] = [
        ("privatbahn_be_kombirail", "BE", lambda: "kombirail" in c),
        ("privatbahn_cz_regiojet", "CZ", lambda: "regiojet" in c),
        ("privatbahn_de_railpool", "DE", lambda: "railpool" in c),
        ("privatbahn_nl_ecco", "NL", lambda: "ecco-rail" in c or "eccorail" in c),
        ("privatbahn_de_mrce", "DE", lambda: "mrce" in c),
        ("privatbahn_cz_lokotrans", "CZ", lambda: "lokotrans" in c),
        ("privatbahn_ch_railadventure", "CH", lambda: "railadventure" in c),
        ("privatbahn_dk_lokaltog", "DK", lambda: "lokaltog" in c),
        ("privatbahn_de_bayernbahn", "DE", lambda: "bayernbahn" in c),
        ("privatbahn_be_solvay", "BE", lambda: "solvay" in c),
        ("privatbahn_de_mkb", "DE", lambda: re.search(r"\bmkb\b", c) is not None),
        ("privatbahn_ch_bls", "CH", lambda: re.search(r"\bbls\b", c) is not None),
        ("privatbahn_be_lineas", "BE", lambda: "lineas" in c),
        ("privatbahn_de_rbh", "DE", lambda: re.search(r"\brbh\b", c) is not None),
        ("privatbahn_de_irp", "DE", lambda: re.search(r"\birp\b", c) is not None),
        ("privatbahn_de_skl", "DE", lambda: re.search(r"\bskl\b", c) is not None),
        ("privatbahn_de_train_charter", "CH", lambda: "train charter" in c),
        ("privatbahn_de_talent2", "DE", lambda: "talent 2" in c or "talent2" in c),
        ("privatbahn_it_pmt", "IT", lambda: "e483 pmt" in c or "pmt vi" in c),
        ("privatbahn_nl_strukton", "NL", lambda: "strukton" in c),
        ("privatbahn_pl_en57", "PL", lambda: "en 57" in c and (" pr" in c or " km" in c or "pkp" in c)),
        ("privatbahn_pl_et21", "PL", lambda: "et 21 ctl" in c or "et21 ctl" in c),
        ("privatbahn_de_altmark", "DE", lambda: "altmark-rail" in c or "altmark rail" in c),
        ("privatbahn_de_bundeswehr", "DE", lambda: "bundeswehr" in c),
        ("privatbahn_de_v23", "DE", lambda: re.search(r"\bv 23\b", c) is not None),
        ("privatbahn_pl_eu07", "PL", lambda: "eu07" in c and " pr" in c),
        ("privatbahn_de_stadler_gtw", "DE", lambda: "gtw 2/6" in c and "stadler" in c and "db" in c),
        ("privatbahn_at_stb", "AT", lambda: "gtw 2/6" in c and "stadler" in c and " stb" in c),
        ("privatbahn_de_hlb", "DE", lambda: "gtw 2/6" in c and "stadler" in c and " hlb" in c),
        ("privatbahn_pl_wisko", "PL", lambda: "pl-wisko" in c or "wiskol" in c or "lotos" in c),
        ("privatbahn_pl_pmp", "PL", lambda: "pmp-pw" in c),
        ("privatbahn_pl_pkp", "PL", lambda: "pkp skm" in c),
        ("privatbahn_pl_ctl", "PL", lambda: "ctl rail" in c or "ctl logistics" in c),
        ("privatbahn_pl_sm42", "PL", lambda: "sm42" in c),
        ("privatbahn_nl_railion_nl", "NL", lambda: "railion logistics nl" in c),
        ("privatbahn_nl_rts", "NL", lambda: "rts-swietelsky nl" in c),
        ("privatbahn_dk_vltj", "DK", lambda: "vltj" in c),
        ("privatbahn_at_hafferl", "AT", lambda: "stern hafferl" in c or "hafferl vi" in c),
        ("privatbahn_at_setg", "AT", lambda: "setg" in c),
        ("privatbahn_at_rcg", "AT", lambda: "railcargogroup" in c),
        ("privatbahn_at_gkb", "AT", lambda: " gkb" in c or "gkb vi" in c),
        ("privatbahn_at_schweerbau", "AT", lambda: "schweerbau" in c),
        ("privatbahn_ch_sersa", "CH", lambda: "sersa" in c),
        ("privatbahn_nl_vsm", "NL", lambda: " vsm" in c or "rh 500 vsm" in c),
        ("privatbahn_sk_stk", "SK", lambda: re.search(r"181\s+stk", c) is not None),
        ("privatbahn_de_medway", "DE", lambda: "medway" in c),
        ("privatbahn_de_captrain", "DE", lambda: "captrain" in c),
        ("privatbahn_de_northrail", "DE", lambda: "northrail" in c),
        ("privatbahn_de_meg", "DE", lambda: " meg" in c or "meg vi" in c),
        ("privatbahn_de_black_dragons", "DE", lambda: "black dragons" in c),
        ("privatbahn_de_beacon", "DE", lambda: "beacon" in c),
        ("privatbahn_de_clr", "DE", lambda: "cargo logistic rail" in c),
        ("privatbahn_de_wfl", "DE", lambda: " wfl" in c or "wfl vi" in c),
        ("privatbahn_de_press", "DE", lambda: ("traxx" in c and "press" in c) or ("br 248" in c and "press" in c) or ("br 140" in c and "press" in c)),
        ("privatbahn_de_hsl", "DE", lambda: " hsl" in c or "hsl logistik" in c),
        ("privatbahn_de_ebs", "DE", lambda: " ebs" in c or "br 312" in c),
        ("privatbahn_de_national_express", "DE", lambda: "national express" in c),
        ("privatbahn_de_wtk", "DE", lambda: "wtk" in c or "v 60 d-2" in c),
        ("privatbahn_pl_wlc", "PL", lambda: " wlc" in c or "wlc vi" in c),
        ("privatbahn_de_alpha_trains", "DE", lambda: "alpha trains" in c),
        ("privatbahn_ch_bern", "CH", lambda: "s-bahn bern" in c or "bern rm" in c),
        ("privatbahn_cs_t435", "CS", lambda: "t435" in c),
        ("privatbahn_dk_midtjyske", "DK", lambda: "midtjyske" in c),
        ("privatbahn_de_railion", "DE", lambda: "railion" in c),
        ("privatbahn_cz_metrans", "CZ", lambda: "metrans" in c),
        ("privatbahn_nl_fyra", "NL", lambda: "fyra" in c),
        ("privatbahn_it_gts", "IT", lambda: "gts" in c and re.search(r"\b191\b", c)),
        ("privatbahn_pl_orlen", "PL", lambda: "orlen" in c),
        ("privatbahn_us_whitcomb", "US", lambda: "whitcomb" in c),
        ("privatbahn_de_slrs", "DE", lambda: "slrs" in c),
        ("privatbahn_hu_gysev", "HU", lambda: "gysev" in c),
        ("privatbahn_nl_arriva", "NL", lambda: "arriva" in c),
        ("privatbahn_pl_ctl232", "PL", lambda: re.search(r"\b232\b", c) and re.search(r"\bctl\b", c)),
        ("privatbahn_de_evb", "DE", lambda: re.search(r"\bevb\b", c)),
        ("privatbahn_cz_cargounit", "CZ", lambda: "cargounit" in c or "cargo unit" in c),
        ("privatbahn_de_traxx_start", "DE", lambda: "traxx start" in c),
    ]
    for rule_id, iso, fn in checks:
        if fn():
            return (rule_id, iso)
    return None


def _propose_era_from_blob(article: Article) -> Optional[tuple[str, str]]:
    """``era`` aus Beschreibung oder erster Titelzeile, wenn leer."""
    model = article.get("model")
    if not isinstance(model, dict):
        return None
    era = model.get("era")
    if era is not None and isinstance(era, str) and era.strip():
        return None
    blob = _text_blob(article)
    em = re.search(r"Epoche:\s*([IVX]+(?:-[IVX]+)*)", blob, re.I)
    if em:
        return ("era_from_description", em.group(1).strip())
    first = blob.split("\n", 1)[0]
    tm = re.search(r"\b(I{1,3}|IV|V|VI)(?:\s|$)", first)
    if tm:
        return ("era_from_title", tm.group(1))
    if re.search(r"\bsu46\b", blob.lower()) and "pkp" in blob.lower():
        return ("era_su46_pkp", "V")
    if "whitcomb" in blob.lower():
        return ("era_whitcomb_us", "III")
    return None


def _propose_sp_operator_era(article: Article) -> Optional[tuple[str, str, Optional[str]]]:
    """SP KM ML 4000: fehlender Operator/Epoche nach Shop-Import (US, Ep. III)."""
    model = article.get("model")
    if not isinstance(model, dict):
        return None
    t = str(model.get("type") or "")
    if not re.search(r"\bSP\s+9", t, re.I):
        return None
    blob = _text_blob(article)
    op_out: Optional[str] = None
    if model.get("operator") is None or (
        isinstance(model.get("operator"), str) and not str(model.get("operator")).strip()
    ):
        op_out = "Southern Pacific"
    era_out: Optional[str] = None
    era = model.get("era")
    if era is None or (isinstance(era, str) and not str(era).strip()):
        em = re.search(r"Epoche:\s*([IVX]+(?:-[IVX]+)*)", blob, re.I)
        if em:
            era_out = em.group(1).strip()
        elif re.search(r"\bIII\b", blob):
            era_out = "III"
        else:
            era_out = "III"
    if op_out is None and era_out is None:
        return None
    return ("sp_km_ml", op_out, era_out)


def propose_country(article: Article) -> Optional[tuple[str, str]]:
    """
    Returns (rule_id, iso_country) or None.
    """
    model = article.get("model")
    if not isinstance(model, dict) or not _country_missing(model):
        return None

    sp = _propose_sp_operator_era(article)
    if sp and _country_missing(model):
        return ("sp_km_ml", "US")

    op = _norm_op(model.get("operator"))
    if not op:
        missing = _propose_missing_operator_fields(article)
        if missing and _country_missing(model) and missing[2]:
            return (missing[0], missing[2])
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

    if op == "Privatbahn":
        return _privatbahn_infer_country(article)

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
        sp_fields = _propose_sp_operator_era(data)
        missing_op = _propose_missing_operator_fields(data)
        era_prop = _propose_era_from_blob(data)
        if not prop and not sp_fields and not missing_op and not era_prop:
            continue
        file_dirty = False
        if missing_op:
            rule_id, new_op, new_c = missing_op
            if new_op and (
                model.get("operator") is None
                or (isinstance(model.get("operator"), str) and not str(model.get("operator")).strip())
            ):
                if not dry_run:
                    model["operator"] = new_op
                    file_dirty = True
                else:
                    print(f"{path}\t{rule_id}\toperator -> {new_op!r}", file=sys.stderr)
            if new_c and _country_missing(model):
                if not dry_run:
                    model["country"] = new_c
                    file_dirty = True
                    changed.append((path, rule_id, new_c))
                else:
                    changed.append((path, rule_id, new_c))
        if prop:
            rule_id, new_c = prop
            old_c = model.get("country")
            if old_c != new_c:
                changed.append((path, rule_id, new_c))
                if not dry_run:
                    model["country"] = new_c
                    file_dirty = True
        if sp_fields:
            _, new_op, new_era = sp_fields
            if new_op and (
                model.get("operator") is None
                or (isinstance(model.get("operator"), str) and not model.get("operator").strip())
            ):
                if not dry_run:
                    model["operator"] = new_op
                    file_dirty = True
                else:
                    print(f"{path}\tsp_km_ml\toperator -> {new_op!r}", file=sys.stderr)
            if new_era and (
                model.get("era") is None
                or (isinstance(model.get("era"), str) and not str(model.get("era")).strip())
            ):
                if not dry_run:
                    model["era"] = new_era
                    file_dirty = True
                else:
                    print(f"{path}\tsp_km_ml\tera -> {new_era!r}", file=sys.stderr)
        if era_prop:
            era_rule, new_era = era_prop
            if new_era and (
                model.get("era") is None
                or (isinstance(model.get("era"), str) and not str(model.get("era")).strip())
            ):
                if not dry_run:
                    model["era"] = new_era
                    file_dirty = True
                else:
                    print(f"{path}\t{era_rule}\tera -> {new_era!r}", file=sys.stderr)
        if file_dirty:
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
