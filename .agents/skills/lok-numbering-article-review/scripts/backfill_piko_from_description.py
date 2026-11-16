#!/usr/bin/env python3
"""
Backfill PIKO article fields from embedded ``description`` text and optional Shop-HTML-Cache.

Fills when leer bzw. Shop-Platzhalter, konservativ:

- ``model.era`` aus ``Epoche:`` / Fliesstext ``Ep. IV``
- ``model.operator`` aus ``Bahnverwaltung:`` (nicht «Privatbahn» überschreiben, wenn Modell schon EVU)
- ``model.country`` aus Operator-Map (Parser-Logik)
- ``model.number`` aus erster Titelzeile (UIC / Betriebsnummer)
- ``model.livery`` aus erster Titelzeile (Sonderlack, nicht Staatsbahn allein)
- ``model.electricSystem`` aus ``Stromsystem:`` + Sound-Hinweis
- ``model.luepMm`` / ``model.minRadiusMm`` aus HTML-Attributen oder Description
- ``model.decoderInterface`` aus ``Digitale Schnittstelle`` / NEM+PluX im Text

HTML-Cache (optional): ``.tmp/import/**/html/{articleNumber}.html`` neben dem Repo-Root.

Usage::

    python3 .agents/skills/lok-numbering-article-review/scripts/backfill_piko_from_description.py articles/piko
    python3 .agents/skills/lok-numbering-article-review/scripts/backfill_piko_from_description.py --apply articles/piko
    python3 ... --tag piko-neuheiten-2023 --apply articles/piko
"""

from __future__ import annotations

import argparse
import html as htmlmod
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


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


def _normalize_piko_operator(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    aliases = {
        "OBB": "ÖBB",
        "CSD": "ČSD",
        "CD": "ČD",
        "DB-AG": "DB AG",
        "DBAG": "DB AG",
    }
    if s in aliases:
        return aliases[s]
    return aliases.get(s.upper(), s)


def _operator_to_country(operator: str, era: Any) -> Optional[str]:
    op = (operator or "").strip().upper()
    table = {
        "DB": "DE",
        "DB AG": "DE",
        "DR": "DE",
        "DRG": "DE",
        "SBB": "CH",
        "ÖBB": "AT",
        "OBB": "AT",
        "NS": "NL",
        "SNCF": "FR",
        "FS": "IT",
        "PKP": "PL",
        "ČSD": "CS",
        "CSD": "CS",
        "ČD": "CZ",
        "CD": "CZ",
        "DSB": "DK",
        "MAV": "HU",
    }
    if op in table:
        cc = table[op]
        if op == "DR" and isinstance(era, str) and era.strip().upper() in {"IV", "V"}:
            return "DD"
        return cc
    for key, cc in table.items():
        if op.startswith(key + " "):
            return cc
    return None


def _canonical_electric_system_from_description(description: str) -> Optional[str]:
    d = description or ""
    m = re.search(r"Stromsystem:\s*([^\n]+)", d, re.I)
    if not m:
        return None
    raw = m.group(1).lower()
    # Nur werkseitiger Sound/Decoder → Digital; «nachrüstbar» allein reicht nicht
    digital = bool(
        re.search(r"Sound ja/nein:\s*ja", d, re.I)
        or re.search(r"Sound-Decoder werkseitig|werkseitig(?: bereits)? über einen .{0,40}Decoder|Soundmodell werkseitig", d, re.I)
        or re.search(r"Verbauter Decoder:", d, re.I)
    )
    if "wechsel" in raw:
        return "AC-Digital" if digital else "AC-Analog"
    if "gleich" in raw:
        if "digital" in raw and "analog" not in raw:
            return "DC-Digital"
        return "DC-Digital" if digital else "DC-Analog"
    return None


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


def _find_html_cache(article_number: str, repo_root: Path) -> Optional[Path]:
    html_dirs = sorted((repo_root / ".tmp" / "import").glob("*/html"))
    for d in html_dirs:
        p = d / f"{article_number}.html"
        if p.is_file():
            return p
    return None


def _parse_html_attrs(html: str) -> dict[str, str]:
    """Extract PIKO shop attribute table keys from a cached PDP."""
    out: dict[str, str] = {}
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    for m in re.finditer(
        r">([^<>]{2,60}?):\s*</(?:t[dh]|div|span|dt)>\s*<(?:t[dh]|div|span|dd)[^>]*>\s*([^<]+)",
        text,
        re.I,
    ):
        key = htmlmod.unescape(m.group(1)).strip()
        val = htmlmod.unescape(m.group(2)).strip()
        if key and val and len(key) < 60:
            out[key] = val
    plain = htmlmod.unescape(re.sub(r"<[^>]+>", "\n", text))
    for key in ("Epoche", "Bahnverwaltung", "Stromsystem", "Sound ja/nein"):
        m = re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$", plain)
        if m and key not in out:
            out[key] = m.group(1).strip()
    m = re.search(r"Mindestradius\s*\[mm\]:\s*(\d+)", plain, re.I)
    if m:
        out["Mindestradius [mm]"] = m.group(1)
    # LüP sits as Maßbezeichnung + Maß [mm]
    if "Maß [mm]" in out and "Maßbezeichnung" in out and "lüp" in out["Maßbezeichnung"].lower():
        out["LüP"] = out["Maß [mm]"]
    m = re.search(r"Digitale Schnittstelle:\s*([^\n]+)", plain, re.I)
    if m:
        out["Digitale Schnittstelle"] = m.group(1).strip()
    return out


def _merge_attrs(desc_attrs: dict[str, str], html_attrs: dict[str, str]) -> dict[str, str]:
    merged = dict(html_attrs)
    merged.update({k: v for k, v in desc_attrs.items() if v})
    return merged


def _era_from_prose(description: str) -> Optional[str]:
    m = re.search(r"\bEp(?:oche|\.)\s*(I{1,3}|IV|V|VI|III-IV|II-III|IV-V|V-VI)\b", description or "", re.I)
    if not m:
        return None
    return m.group(1).upper().replace("III-IV", "III-IV")


def _decoder_from_text(blob: str) -> Optional[str]:
    b = blob or ""
    if re.search(r"NEM\s*658\s*PluX22|PluX22[^\n]{0,40}NEM\s*658|Schnittstelle nach NEM 658", b, re.I):
        return "NEM 658 PluX22"
    if re.search(r"\b20[- ]?polig", b, re.I):
        return "20polig"
    if re.search(r"NEM\s*658", b, re.I):
        return "NEM 658 PluX22"
    if re.search(r"PluX22", b, re.I):
        return "NEM 658 PluX22"
    m = re.search(r"Digitale Schnittstelle:\s*([^\n]+)", b, re.I)
    if m:
        return m.group(1).strip()
    return None


def _livery_from_prose(description: str) -> Optional[str]:
    """Only high-confidence prose patterns (no marketing sentences)."""
    d = description or ""
    m = re.search(r"[„«\"]([^„\"»”]{2,40})[“\"»”]", d)
    if m:
        s = m.group(1).strip()
        low = s.lower()
        if low in {"roncalli", "gorch fock", "laminátka", "laminatka", "bigrigio", "klimaschützer", "klimaschuetzer"}:
            if "lamin" in low:
                return "Laminátka"
            if "klima" in low:
                return "Klimaschützer"
            return s
        if re.search(r"\b(neuheit|set mit|ausführung|ep\.|bullauge)\b", low):
            return None
        if any(ch.isalpha() for ch in s) and " " not in s and len(s) <= 24:
            return s
    m = re.search(
        r"\bin\s+(beigeblau(?:er|en)?|gelb-grau(?:er|en)?|blaubeige(?:r|n)?|blau(?:er|en)?)\s+Lackierung\b",
        d,
        re.I,
    )
    if m:
        raw = m.group(1).lower()
        for stem in ("beigeblau", "gelb-grau", "blaubeige", "blau"):
            if raw.startswith(stem):
                return stem
    m = re.search(r"\bŠkoda\s+47E\s+[„\"]Laminátka[“\"]", d, re.I)
    if m:
        return "Laminátka"
    return None


def _first_line_is_marketing(first: str) -> bool:
    f = (first or "").strip()
    return bool(re.match(r"^Neuheit\b", f, re.I)) or len(f) > 120


def _missing_str(val: Any) -> bool:
    return val is None or (isinstance(val, str) and not val.strip()) or val == "Unbekannt"


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


def _apply_backfill(article: dict[str, Any], *, html_attrs: Optional[dict[str, str]] = None) -> list[str]:
    changes: list[str] = []
    desc = article.get("description") or ""
    model = article.get("model")
    if not isinstance(model, dict):
        return changes
    if not desc.strip() and not html_attrs:
        return changes

    attrs = _merge_attrs(_parse_description_attrs(desc), html_attrs or {})
    first = _first_title_line(desc)
    blob = desc + "\n" + "\n".join(f"{k}: {v}" for k, v in attrs.items())

    era_raw = attrs.get("Epoche", "").strip() or (_era_from_prose(desc) or "")
    if era_raw and _missing_str(model.get("era")):
        changes.append(f"era: {model.get('era')!r} -> {era_raw!r}")
        model["era"] = era_raw

    desc_op_raw = attrs.get("Bahnverwaltung", "").strip()
    desc_op = _normalize_piko_operator(desc_op_raw) if desc_op_raw else ""
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
        mapped = _operator_to_country(_normalize_piko_operator(op_for_country), era_for_country)
        if mapped:
            changes.append(f"country: {model.get('country')!r} -> {mapped!r}")
            model["country"] = mapped

    if _missing_str(model.get("number")):
        prop_n = _propose_number(first, str(model.get("type") or ""))
        if prop_n:
            changes.append(f"number: {model.get('number')!r} -> {prop_n!r}")
            model["number"] = prop_n
    else:
        prop_n = str(model.get("number") or "").strip() or None

    if _missing_str(model.get("livery")):
        prop_l = None
        if first and not _first_line_is_marketing(first):
            prop_l = _propose_livery(
                first,
                str(model.get("type") or ""),
                model.get("operator") if isinstance(model.get("operator"), str) else None,
                prop_n if prop_n else _propose_number(first, str(model.get("type") or "")),
            )
        if not prop_l:
            prop_l = _livery_from_prose(desc)
        if prop_l and not re.search(
            r"\b(neuheit|güterwagen|bettung|attraktiv|dachlandschaft|bullaugen?|ausführung|set mit|"
            r"staatsbahn|baureihe|als baureihe)\b",
            prop_l,
            re.I,
        ):
            changes.append(f"livery: {model.get('livery')!r} -> {prop_l!r}")
            model["livery"] = prop_l

    # electricSystem: prefer structured Stromsystem from attrs/description
    es = None
    if attrs.get("Stromsystem") or "Stromsystem:" in desc:
        synth = desc
        if attrs.get("Stromsystem") and "Stromsystem:" not in synth:
            synth = f"{synth}\nStromsystem: {attrs['Stromsystem']}"
        if attrs.get("Sound ja/nein") and "Sound ja/nein:" not in synth:
            synth = f"{synth}\nSound ja/nein: {attrs['Sound ja/nein']}"
        es = _canonical_electric_system_from_description(synth)
    if es and model.get("electricSystem") != es:
        changes.append(f"electricSystem: {model.get('electricSystem')!r} -> {es!r}")
        model["electricSystem"] = es

    # decoderInterface
    if _missing_str(model.get("decoderInterface")):
        di = attrs.get("Digitale Schnittstelle", "").strip() or (_decoder_from_text(blob) or "")
        if di.lower() in {"nicht vorhanden", "ohne", "kein", "-"}:
            di = "Unbekannt"
        if di:
            changes.append(f"decoderInterface: {model.get('decoderInterface')!r} -> {di!r}")
            model["decoderInterface"] = di

    # luepMm / minRadiusMm
    if model.get("luepMm") is None:
        raw = attrs.get("LüP") or attrs.get("Maß [mm]")
        if raw and re.fullmatch(r"\d+", str(raw).strip()):
            val = int(str(raw).strip())
            # Skip absurd set lengths unless already triebzug-sized intentional; still allow >1000 for ICE
            changes.append(f"luepMm: {model.get('luepMm')!r} -> {val!r}")
            model["luepMm"] = val
    if model.get("minRadiusMm") is None:
        raw = attrs.get("Mindestradius [mm]") or attrs.get("Mindestradius")
        if raw and re.fullmatch(r"\d+", str(raw).strip()):
            val = int(str(raw).strip())
            changes.append(f"minRadiusMm: {model.get('minRadiusMm')!r} -> {val!r}")
            model["minRadiusMm"] = val

    return changes


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path, default=[Path("articles/piko")])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--tag",
        metavar="SLUG",
        action="append",
        default=None,
        help="Nur Artikel mit diesem Tag (mehrfach möglich).",
    )
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo-Root für .tmp/import/*/html Cache (Default: CWD).",
    )
    args = ap.parse_args(argv)
    repo_root = (args.repo_root or Path.cwd()).expanduser().resolve()
    files = _walk([p.expanduser().resolve() for p in args.paths])
    tag_set = set(args.tag) if args.tag else None
    updated = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: {path}: {e}", file=sys.stderr)
            return 1
        if tag_set:
            tags = set(data.get("tags") or [])
            if not tags.intersection(tag_set):
                continue
        art_no = str(data.get("articleNumber") or path.stem)
        html_path = _find_html_cache(art_no, repo_root)
        html_attrs: dict[str, str] = {}
        if html_path is not None:
            try:
                html_attrs = _parse_html_attrs(html_path.read_text(encoding="utf-8", errors="replace"))
            except OSError as e:
                print(f"warn: {html_path}: {e}", file=sys.stderr)
        changes = _apply_backfill(data, html_attrs=html_attrs)
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
    else:
        print("\nDry-run: re-run with --apply to write.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
