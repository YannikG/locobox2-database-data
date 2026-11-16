#!/usr/bin/env python3
"""
Autofix REE Modèles Shop-Importreste (Allowlist, konservativ).

- ``model.type`` / ``model.number``: SNCF ``BB``/``CC`` Serie vs. Laufnummer
  (auch wenn ``number`` noch den Präfix trägt, z. B. ``BB 9282`` / ``BB 9282``).
  Siehe ``reference-sncf-type-number.md``.
- Dampf ``MACHINE …-231K/G …`` / ``Locomotive à vapeur …`` → ``231 K`` / ``231 G``
  + laufende Nummer; Kategorie ``dampflokomotive``.
- ``141 D 318`` → ``141 D`` + ``318``.
- Lange Shop-Titel (``[HO]``, Epoche, Analog/DCC) → Kurztyp wenn eindeutig
  (Moyse, 040 DE, CFL 852, RGP).
- ``operator`` / ``era`` aus Beschreibung wenn noch ``Unbekannt``.
- ``model.livery`` aus Beschreibung wenn noch leer (Anführungszeichen,
  ``livrée …``, Farb-/Schema-Kurzphrasen wie ``vert 301``, ``Rouge TEE``).
- HOm-Personenwagen fälschlich als Triebwagen → Finding-safe Kategorie ``wagen``.

Usage::

    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_ree_shop_import.py articles/ree
    python3 .agents/skills/lok-numbering-article-review/scripts/autofix_ree_shop_import.py --apply articles/ree
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

Article = dict[str, Any]

_ERA_IN_TEXT = re.compile(
    r"\bEp\.?\s*(I{1,3}|IV|VI{0,2}|V)(?:\s*[-/]\s*(I{1,3}|IV|VI{0,2}|V))?\b",
    re.I,
)
_BBCC = re.compile(r"^(BB|CC)\s+(\d{3,5})$", re.I)
_BBCC_ANY = re.compile(r"\b((?:BB|CC)\s*\d{3,5})\b", re.I)
_STEAM_MACHINE = re.compile(
    r"(?:MACHINE|Locomotive\s+à\s+vapeur)\s+"
    r"(?:(\d)\s*[-–—]\s*)?"
    r"(\d{3})\s*([A-Z])\s*(\d{1,4})\b",
    re.I,
)
_STEAM_141 = re.compile(r"\b(141)\s*([A-Z])\s*(\d{2,4})\b", re.I)
_MOYSE = re.compile(
    r"Locotracteur\s+Moyse\s+(\d+\s*TDE)(?:\s+([^,]+))?",
    re.I,
)
_040_DE = re.compile(r"\b040\s*DE\s*(\d{1,4})\b", re.I)
_CFL_852 = re.compile(r"\b(?:Locomotive\s+diesel\s+)?852\b.*\bCFL\b", re.I)

_LIVERY_QUOTED = re.compile(r"[“\"«]([^”\"»]{2,40})[”\"»]")
_LIVERY_LIVREE = re.compile(
    r"\b[Ll]ivr[ée]e\s+(.+?)(?="
    r"\s*,|"  # Depot / Logos / Ep. folgen meist nach Komma
    r"\s+Ep\.|"
    r"\s*[-–—]\s*(?:ANALOG|DCC|DIGITAL|AC\s+SOUND)|"
    r"$)",
    re.I,
)
_LIVERY_PHRASE = re.compile(
    r"\b("
    # längere Farb-/Schema-Phrasen zuerst
    r"Origine rouge et cr[eè]me|"
    r"rouge\s*/\s*cr[eè]me|rouge et cr[eè]me|"
    r"bleu\s*/\s*gris\s+Perle|"
    r"Jaune et blanche|"
    r"Orange(?:\s*[-–]?\s*Alu|\s+B[ée]ton)|"
    r"Verte(?:\s+Origine(?:\s+Interphonie)?)?(?:\s+avec\s+enjoliveur)?|"
    r"Bleue(?:\s+[A-Za-zÀ-ÿ]+)?|"
    r"Rouge(?:\s+(?:TEE|SNCF|Capitole))|"
    r"modernis[ée]+\s+Rouge|"
    r"Couleur d['’]origine|"
    r"vert\s*30[16]|"
    r"GRG|RG(?:\s+Marquages\s+jaunes)?|"
    r"[Jj]up[ée]e?(?:\s*,\s*1[èe]re(?:/2nde)?\s+classes?(?:\s+Origine)?)?|"
    r"Industr?iel\s+vert\s*30[16]|Indutriel\s+vert\s*30[16]|"
    r"B[ée]ton(?:\s+Beffara)?|"
    r"Vert(?=\s*,)|"
    # nacktes Rouge/Vert nur wenn kein /-Farbpaar folgt
    r"Rouge(?!\s*/)|"
    r"vert(?!\s*/)"
    r")\b",
    re.I,
)
_LIVERY_NAMED = re.compile(
    r"\b(FRET|Multiservice(?:s)?|Corail|Arzens|Capitole|Isabelle|"
    r"En Voyage|LA POSTE|RECORD DU MONDE|Cage à Poule|Transports Réunis|"
    r"Mistral|atlantique)\b",
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


def _is_ree(article: Article) -> bool:
    if (article.get("manufacturer") or "").strip().upper() in ("REE", "REE MODÈLES", "REE MODELES"):
        return True
    url = ((article.get("source") or {}).get("url") or "").lower()
    return "ree-store.com" in url or "ree-modeles.com" in url


def _norm_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def sncf_series_and_running(prefix: str, digits: str) -> tuple[str, Optional[str]]:
    """
    Map SNCF BB/CC digit block → (series type, running number or None for pure series).

    Special REE families (BB 9300 / 25100 / 25200) before generic //1000 or //100.
    """
    pref = prefix.upper()
    d = digits.strip()
    if not d.isdigit():
        return f"{pref} {d}", d

    if pref == "BB":
        if len(d) == 5 and d.startswith("251"):
            return "BB 25100", None if d == "25100" else d
        if len(d) == 5 and d.startswith("252"):
            return "BB 25200", None if d == "25200" else d
        if len(d) == 4 and d.startswith("93"):
            return "BB 9300", None if d == "9300" else d

    if len(d) == 5:
        if d.endswith("000"):
            return f"{pref} {d}", None
        series = str((int(d) // 1000) * 1000)
        return f"{pref} {series}", None if d == series else d
    if len(d) == 4:
        if d.endswith("00"):
            return f"{pref} {d}", None
        series = str((int(d) // 100) * 100)
        return f"{pref} {series}", None if d == series else d
    if len(d) == 3:
        # HOm BB 400 etc.: series stays in type; compact «BB400» → number «400»
        return f"{pref} {d}", d
    return f"{pref} {d}", d


def _parse_bbcc_token(token: str) -> Optional[tuple[str, str]]:
    t = _norm_spaces(token.replace("BB", "BB ").replace("CC", "CC "))
    t = _norm_spaces(t)
    # Compact shop form «BB400»
    m = re.fullmatch(r"(BB|CC)(\d{3,5})", t, re.I)
    if m:
        return m.group(1).upper(), m.group(2)
    m = _BBCC.fullmatch(t)
    if not m:
        m = re.fullmatch(r"(BB|CC)\s*(\d{3,5})", t, re.I)
    if not m:
        return None
    return m.group(1).upper(), m.group(2)


def propose_sncf_type_number(model: dict[str, Any]) -> Optional[tuple[str, str, Optional[str]]]:
    """Return (rule, new_type, new_number) or None."""
    t = model.get("type")
    n = model.get("number")
    if not isinstance(t, str) or not t.strip():
        return None
    t0 = _norm_spaces(t)

    # Case A: type is pure BB/CC + digits (number null, same, or prefixed)
    parsed_t = _parse_bbcc_token(t0)
    if parsed_t:
        pref, dig = parsed_t
        # HOm BB 400 with concrete unit number (402, 040-003) — do not collapse to «400»
        if pref == "BB" and dig == "400" and isinstance(n, str):
            n0 = _norm_spaces(n)
            if n0 not in ("400", "BB400", "BB 400") and re.fullmatch(
                r"\d{2,3}(?:-\d{3})?", n0
            ):
                return None
        series, running = sncf_series_and_running(pref, dig)
        if isinstance(n, str) and n.strip():
            n0 = _norm_spaces(n)
            parsed_n = _parse_bbcc_token(n0)
            if parsed_n:
                _np, nd = parsed_n
                series2, running2 = sncf_series_and_running(_np, nd)
                # Prefer number token as running source when both present
                series, running = series2, running2
            elif n0.isdigit() and len(n0) >= 4:
                series, running = sncf_series_and_running(pref, n0)
            # else keep series from type, strip bad number below
        if series != t0 or (running or None) != (n if n not in ("", None) else None):
            # also when number was "BB 9282" and should become "9282"
            if isinstance(n, str) and _parse_bbcc_token(_norm_spaces(n)):
                return ("ree_sncf_bbcc_repair", series, running)
            if n is None and running is not None:
                return ("ree_sncf_bbcc_split", series, running)
            if n is None and running is None and series != t0:
                return ("ree_sncf_bbcc_series", series, None)
            if isinstance(n, str) and n.strip() != (running or ""):
                return ("ree_sncf_bbcc_repair", series, running)
        return None

    # Case B: long title still containing BB/CC running number
    if len(t0) > 20:
        m = _BBCC_ANY.search(t0)
        if m:
            parsed = _parse_bbcc_token(m.group(1))
            if parsed:
                pref, dig = parsed
                series, running = sncf_series_and_running(pref, dig)
                if n is None or (isinstance(n, str) and _parse_bbcc_token(n)):
                    return ("ree_sncf_bbcc_from_title", series, running)
    return None


def propose_steam(model: dict[str, Any], desc: str) -> Optional[tuple[str, str, Optional[str]]]:
    blob = f"{model.get('type') or ''} {desc}"
    m = _STEAM_MACHINE.search(blob)
    if m:
        region, wheel, letter, eng = m.group(1), m.group(2), m.group(3).upper(), m.group(4)
        typ = f"{wheel} {letter}"
        num = f"{region}-{eng}" if region else eng
        return ("ree_steam_pacific", typ, num)
    m = _STEAM_141.search(blob)
    if m and re.search(r"vapeur|MACHINE|141\s*[A-Z]", blob, re.I):
        return ("ree_steam_141", f"{m.group(1)} {m.group(2).upper()}", m.group(3))
    return None


def propose_short_titles(model: dict[str, Any], desc: str) -> Optional[tuple[str, str, Optional[str], Optional[str]]]:
    """(rule, type, number, livery_or_none)."""
    t = model.get("type")
    if not isinstance(t, str):
        return None
    blob = f"{t} {desc}"
    n = model.get("number")

    if re.search(r"\brgp\s*1\b", blob, re.I):
        mx = re.search(r"\bX[-\s]?(\d{3,4})\b", blob, re.I)
        num = f"X-{mx.group(1)}" if mx else (n if isinstance(n, str) else None)
        if t.strip() != "RGP 1" or (mx and n != num):
            return ("ree_rgp1", "RGP 1", num, None)

    if re.search(r"\brgp\s*2\b", blob, re.I):
        mx = re.search(r"\bX[-\s]?(\d{3,4})\b", blob, re.I)
        num = f"X-{mx.group(1)}" if mx else (n if isinstance(n, str) else None)
        if t.strip() != "RGP 2" or (mx and n != num) or len(t) > 20:
            return ("ree_rgp2", "RGP 2", num, None)

    # X 2800 series (jupé / origine): running X-28xx/29xx, never the class «2800» alone
    if re.search(r"\bAutorail\s+X|\bX\s*-?\s*2[89]\d{2}\b", blob, re.I) and re.search(
        r"\bX\s*-?\s*2[89]\d{2}\b", desc, re.I
    ):
        mx = re.search(r"\bX\s*-?\s*(2[89]\d{2})\b", desc, re.I)
        if mx and mx.group(1) != "2800":
            num = f"X-{mx.group(1)}"
            if t.strip() != "X 2800" or n != num or len(t) > 20:
                return ("ree_x2800", "X 2800", num, None)

    # Y 2100 / Y 2200 locotracteurs: prefer unit Y-2249 over series Y 2200 in type
    if re.search(r"Locotracteur|Y-\d{4}", blob, re.I):
        units = re.findall(r"\bY[-\s]?(\d{4})\b", desc, flags=re.I)
        dig = None
        for cand in units:
            if cand not in ("2100", "2200"):
                dig = cand
                break
        if dig is None and units:
            dig = units[0]
        if dig:
            series = "Y 2100" if dig.startswith("21") else ("Y 2200" if dig.startswith("22") else "Y")
            if len(t) > 15 or t.startswith("[HO]") or n != dig:
                return ("ree_y_tracteur", series, dig, None)

    # OCR letter O in CC 71O6
    if re.search(r"\bCC\s*71O\d\b", blob, re.I):
        mo = re.search(r"\bCC\s*71O(\d)\b", blob, re.I)
        if mo:
            dig = f"710{mo.group(1)}"
            return ("ree_ocr_cc710x", "CC 7100", dig, None)

    mm = _MOYSE.search(blob)
    if mm:
        typ = f"Moyse { _norm_spaces(mm.group(1)) }"
        liv = _norm_spaces(mm.group(2)) if mm.group(2) else None
        if liv and re.search(r"\bEp\.|Analog|DCC|DC\b", liv, re.I):
            liv = None
        if len(t) > 25 or t.startswith("[HO]"):
            return ("ree_moyse", typ, n if isinstance(n, str) else None, liv)

    m040 = _040_DE.search(blob)
    if m040:
        typ = f"040 DE {m040.group(1)}"
        if len(t) > 20 or "Locomotive diesel" in t:
            return ("ree_040_de", typ, m040.group(1), None)

    if _CFL_852.search(blob):
        if len(t) > 15 or t.startswith("[HO]"):
            return ("ree_cfl_852", "852", "852", None)

    return None


def _livery_empty(liv: Any) -> bool:
    return liv in (None, "", "Unbekannt", "unbekannt", "null")


def _clean_livery(raw: str) -> Optional[str]:
    s = _norm_spaces(raw).strip(" ,;-–—")
    s = re.sub(
        r"\s*(?:,|\s)\s*(?:Ep\.|Analog|DCC|ACS?|Sound|3 rails|SNCF)\b.*$",
        "",
        s,
        flags=re.I,
    )
    s = _norm_spaces(s).strip(" ,;-–—")
    if not s or len(s) > 40:
        return None
    if re.fullmatch(r"\d+", s):
        return None
    # Shop-Tippfehler / Industriel-Prefix → kanonisch wie bestehende «vert 306»
    m_ind = re.match(r"(?i)^Industr?iel\s+(vert\s*30[16])$", s) or re.match(
        r"(?i)^Indutriel\s+(vert\s*30[16])$", s
    )
    if m_ind:
        return _norm_spaces(m_ind.group(1))
    if re.fullmatch(r"(?i)d['’]origine", s):
        return "Origine"
    if re.fullmatch(r"(?i)atlantique(?:\s+SNCF)?", s):
        return "atlantique"
    # Jupé-Titel: nur Lackwort behalten
    m_jupe = re.match(r"(?i)^(Jup[ée]e?)(?:\s*,.*)?$", s)
    if m_jupe:
        return "Jupé"
    return s


def propose_livery_from_description(model: dict[str, Any], desc: str) -> Optional[str]:
    """Short livery from shop title/description when ``model.livery`` is empty."""
    if not _livery_empty(model.get("livery")):
        return None
    blob = desc or ""
    if not blob.strip():
        return None

    m = _LIVERY_QUOTED.search(blob)
    if m:
        v = _clean_livery(m.group(1))
        if v:
            return v

    m = _LIVERY_LIVREE.search(blob)
    if m:
        v = _clean_livery(m.group(1))
        if v:
            return v

    m = _LIVERY_PHRASE.search(blob)
    if m:
        v = _clean_livery(m.group(1))
        if v:
            return v

    m = _LIVERY_NAMED.search(blob)
    if m:
        return m.group(1)

    return None


def propose_meta(article: Article) -> list[tuple[str, str, Any]]:
    """List of (rule, field_path, new_value)."""
    out: list[tuple[str, str, Any]] = []
    model = article.get("model") or {}
    desc = article.get("description") or ""
    blob = f"{desc} {model.get('type') or ''}"

    liv = propose_livery_from_description(model, desc)
    if liv:
        out.append(("ree_livery_from_desc", "model.livery", liv))

    op = model.get("operator")
    if op in (None, "", "Unbekannt", "unbekannt"):
        if re.search(r"\bSNCF\b", blob):
            out.append(("ree_op_sncf", "model.operator", "SNCF"))
        elif re.search(r"\bCFL\b", blob):
            out.append(("ree_op_cfl", "model.operator", "CFL"))
        elif re.search(r"\bCFD\b", blob):
            out.append(("ree_op_cfd", "model.operator", "CFD"))
        elif re.search(r"\bCFC\b|Chemin de [Ff]er de Corse", blob):
            out.append(("ree_op_cfc", "model.operator", "CFC"))
        elif (model.get("country") or "") == "FR" and re.match(
            r"^(BB|CC|RGP|TGV|X 2800|040 DE|Y \d)\b",
            str(model.get("type") or ""),
        ):
            # REE H0 SNCF-Serien ohne Compagnie-Prop im Shop
            if not re.search(
                r"\b(CFL|CFD|CFC|Industrie|Transports Réunis|Provence)\b",
                blob,
                re.I,
            ):
                out.append(("ree_op_sncf_default", "model.operator", "SNCF"))

    country = model.get("country")
    if country in (None, "", "Unbekannt") and any(
        x[0].startswith("ree_op_sncf") for x in out
    ):
        out.append(("ree_country_fr", "model.country", "FR"))
    if any(x[0] == "ree_op_cfl" for x in out) and country in (None, "", "Unbekannt"):
        out.append(("ree_country_lu", "model.country", "LU"))

    era = model.get("era")
    if era in (None, "", "Unbekannt", "unbekannt"):
        em = _ERA_IN_TEXT.search(blob)
        if em:
            a, b = em.group(1).upper(), em.group(2)
            val = f"{a}-{b.upper()}" if b else a
            # normalize IIII etc already via regex
            out.append(("ree_era_from_text", "model.era", val))

    # electricSystem: REE SKU suffix is authoritative (Analog / S / SAC)
    es = model.get("electricSystem")
    if es in (None, "", "Unbekannt", "unbekannt"):
        art = str(article.get("articleNumber") or "").strip()
        if not art:
            # id ree-MB-050 → MB-050
            aid = str(article.get("id") or "")
            if aid.startswith("ree-"):
                art = aid[4:]
        sug = None
        if art.endswith("SAC"):
            sug = "AC-Digital"
        elif art.endswith("S"):
            sug = "DC-Digital"
        elif art:
            # base SKU: Analog/DC in text, or no digital markers
            if re.search(r"\bACS?\b|AC Sound|3 rails|DCCS?\b|DCC Sound|\bdigital\b", blob, re.I):
                if re.search(r"\bACS?\b|AC Sound|3 rails", blob, re.I):
                    sug = "AC-Digital"
                elif re.search(r"\bDCCS?\b|DCC Sound|\bdigital\b", blob, re.I):
                    sug = "DC-Digital"
            if sug is None and re.search(r"\banalog(?:ique)?\b|\bDC\b", blob, re.I):
                sug = "DC-Analog"
            if sug is None:
                # REE catalogue base references are 2-rail analog
                sug = "DC-Analog"
        if sug:
            out.append(("ree_es_from_sku", "model.electricSystem", sug))

    # HOm BB400 with N°405 / N°040-003 in description
    if str(model.get("type") or "") == "BB 400":
        mn = re.search(r"\bN[°ºo]\s*(\d{2,3}(?:-\d{3})?)\b", desc, re.I)
        if mn and model.get("number") != mn.group(1):
            out.append(("ree_bb400_unit", "model.number", mn.group(1)))

    cats = article.get("categories")
    if isinstance(cats, list):
        if re.search(r"vapeur|MACHINE\s+\d|231\s*[KG]|141\s*[A-Z]|dampf", blob, re.I):
            if "dampflokomotive" not in cats:
                new_cats = list(cats)
                if "lokomotive" not in new_cats:
                    new_cats.insert(0, "lokomotive")
                if "dampflokomotive" not in new_cats:
                    new_cats.append("dampflokomotive")
                # drop wrong drive cats
                new_cats = [
                    c
                    for c in new_cats
                    if c
                    not in (
                        "diesellokomotive",
                        "elektrolokomotive",
                        "dieseltriebwagen",
                        "elektrotriebwagen",
                        "triebwagen",
                    )
                ]
                out.append(("ree_cat_dampf", "categories", new_cats))
        if re.search(r"\bVoiture\b", str(model.get("type") or ""), re.I) and "triebwagen" in cats:
            out.append(("ree_cat_voiture", "categories", ["wagen"]))
    return out


def propose(article: Article) -> list[tuple[str, str, Any]]:
    """Flattened changes as (rule, dotted_path_or_special, value)."""
    if not _is_ree(article):
        return []
    model = article.get("model")
    if not isinstance(model, dict):
        return []
    desc = str(article.get("description") or "")
    changes: list[tuple[str, str, Any]] = []

    sncf = propose_sncf_type_number(model)
    if sncf:
        rule, nt, nn = sncf
        if nt != model.get("type"):
            changes.append((rule + ":type", "model.type", nt))
        if nn != model.get("number"):
            changes.append((rule + ":number", "model.number", nn))
    else:
        steam = propose_steam(model, desc)
        if steam:
            rule, nt, nn = steam
            if nt != model.get("type"):
                changes.append((rule + ":type", "model.type", nt))
            if nn != model.get("number"):
                changes.append((rule + ":number", "model.number", nn))
        else:
            short = propose_short_titles(model, desc)
            if short:
                rule, nt, nn, liv = short
                if nt != model.get("type"):
                    changes.append((rule + ":type", "model.type", nt))
                if nn != model.get("number"):
                    changes.append((rule + ":number", "model.number", nn))
                if liv and not model.get("livery"):
                    changes.append((rule + ":livery", "model.livery", liv))

    changes.extend(propose_meta(article))
    # One write per field (first wins: type/number rules before meta livery)
    seen: set[str] = set()
    deduped: list[tuple[str, str, Any]] = []
    for rule, field, val in changes:
        if field in seen:
            continue
        seen.add(field)
        deduped.append((rule, field, val))
    return deduped


def _set_path(article: Article, path: str, value: Any) -> None:
    if path == "categories":
        article["categories"] = value
        return
    if path.startswith("model."):
        key = path.split(".", 1)[1]
        model = article.setdefault("model", {})
        model[key] = value
        return
    raise KeyError(path)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.apply and args.dry_run:
        print("error: use only one of --apply or --dry-run", file=sys.stderr)
        return 2
    dry = not args.apply

    files = _walk(args.paths)
    n_files = 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        ch = propose(data)
        if not ch:
            continue
        n_files += 1
        for rule, field, val in ch:
            print(f"{path}\t{rule}\t{field}\t{val!r}")
        if not dry:
            for _rule, field, val in ch:
                _set_path(data, field, val)
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    if dry and n_files:
        print(
            f"\n{n_files} file(s) would change; re-run with --apply to write.",
            file=sys.stderr,
        )
    elif dry:
        print("No changes.", file=sys.stderr)
    else:
        print(f"Updated {n_files} file(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
