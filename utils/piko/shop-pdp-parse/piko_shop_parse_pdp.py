#!/usr/bin/env python3
"""
Parse PIKO Shop PDP HTML (gespeichert aus Chrome / MCP). Kein HTTP im CLI.

Extrahiert u. a. ``og:title``, PDP-``h1`` → ``model.type`` (Rohbezeichnung), ``og:description``, Hauptbild ``img.product__img`` (sonst ``og:image``), groben Preis aus
sichtbarem Text, schreibt optional ``articles/piko/{articleNumber}.json``.

Schweizer Textnormalisierung: «ß» → «ss».
"""

from __future__ import annotations

import argparse
import html as html_lib
import importlib.util
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ARTICLES = _REPO_ROOT / "articles" / "piko"


def swiss_text(s: str) -> str:
    return s.replace("\u00df", "ss").replace("ß", "ss")


def _meta_content(html: str, prop: str) -> Optional[str]:
    m = re.search(
        rf'<meta\s+property=["\']{re.escape(prop)}["\']\s+content=["\']([^"\']+)["\']',
        html,
        re.I | re.S,
    )
    if m:
        return html_lib.unescape(m.group(1).strip())
    m2 = re.search(
        rf'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']{re.escape(prop)}["\']',
        html,
        re.I | re.S,
    )
    if m2:
        return html_lib.unescape(m2.group(1).strip())
    return None


def _price_amount(html: str, canonical: str) -> float:
    """Heuristik: erster «…,… €» oder «… €» im sichtbaren Bereich."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    for pat in (
        r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€",
        r"(\d+,\d{2})\s*€",
        r"€\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
    ):
        m = re.search(pat, text)
        if m:
            raw = m.group(1)
            raw = re.sub(r"\.(?=\d{3},)", "", raw).replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                continue
    return 0.0


def _abs_url(base: str, maybe: str) -> str:
    u = (maybe or "").strip()
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith(("http://", "https://")):
        return u
    return urljoin(base, u)


def _product_main_image_url(html: str, base_url: str) -> str:
    """Hauptbild aus ``<img class=\"product__img\" … src=\"…\">`` (relativ → absolut)."""
    for m in re.finditer(r"<img\b[^>]+>", html, re.I):
        tag = m.group(0)
        if "product__img" not in tag:
            continue
        sm = re.search(r'\bsrc=["\']([^"\']+)["\']', tag, re.I)
        if sm:
            return _abs_url(base_url, sm.group(1).strip())
    return ""


def _html_to_plain(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    t = re.sub(r"<script[^>]*>.*?</script>", " ", t, flags=re.I | re.S)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.I | re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html_lib.unescape(t)
    return re.sub(r"[ \t\r\f\v]+", " ", t).replace(" \n ", "\n").strip()


def _strip_piko_shop_title_suffix(s: str) -> str:
    """Marketing-Suffixe vom Shop-``og:title`` entfernen (Produktzeile für ``model.type``)."""
    s = (s or "").strip()
    if not s:
        return ""
    s = re.sub(r"\s*\|\s*PIKO Webshop\s*$", "", s, flags=re.I)
    s = re.sub(r"\s+Modelleisenbahn\s+kaufen\s*$", "", s, flags=re.I)
    return s.strip()


def _product_type_line_from_html(html: str, og_title: str) -> Optional[str]:
    """
    Roh-Produktbezeichnung (z. B. «E-Lok BR 184.1 DB IV») für ``model.type``.
    Später per Skill in Baureihe/Nummer/Livree zerlegbar.
    """
    for m in re.finditer(r"<h1\b[^>]*>(.*?)</h1>", html, re.I | re.S):
        t = swiss_text(_html_to_plain(m.group(1)))
        if len(t) < 4:
            continue
        low = t.lower()
        if low in ("startseite", "fehler", "404", "seite nicht gefunden"):
            continue
        return t
    raw = (og_title or "").strip() or (_meta_content(html, "og:title") or "")
    bt = _strip_piko_shop_title_suffix(raw)
    return bt or None


def _parse_product_attributes_table(html: str) -> dict[str, str]:
    """
    PDP-Tabelle (u. a. ``#product-attributes``): ``attribute-desc`` / ``attribute-value``-Paare.
    Gesamtes HTML, damit kein fragiles Block-Cropping nötig ist.
    """
    out: dict[str, str] = {}
    for mo in re.finditer(
        r'<td\s+class=["\']attribute-desc["\'][^>]*>(.*?)</td>\s*'
        r'<td\s+class=["\']attribute-value["\'][^>]*>(.*?)</td>',
        html,
        re.I | re.S,
    ):
        key = _html_to_plain(mo.group(1)).rstrip(":").strip()
        val = _html_to_plain(mo.group(2))
        if key and val:
            out[key] = val
    return out


def _normalize_piko_operator(operator: str) -> str:
    """Shop-Schreibweisen auf übliche Kurzformen (Locobox-Konvention)."""
    s = (operator or "").strip()
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    if s == "DB AG":
        return "DB"
    compact = re.sub(r"\s+", "", s).upper()
    if compact == "OBB" and "Ö" not in s and "ö" not in s:
        return "ÖBB"
    return s


_DR_ERA_DE_ONLY = re.compile(r"^(I|II|III)(-(I|II|III))*$", re.I)


def _dr_country_from_era(era_raw: Optional[str]) -> str:
    """DDR-Reichsbahn: Epoche IV → DD; reine I–III → DE; sonst konservativ DD (wie Autofix-Skill)."""
    if not isinstance(era_raw, str) or not era_raw.strip():
        return "DD"
    eu = era_raw.strip().upper().replace(" ", "")
    if "IV" in eu:
        return "DD"
    if _DR_ERA_DE_ONLY.fullmatch(eu):
        return "DE"
    return "DD"


def _operator_to_country(operator: str, era: Optional[str] = None) -> Optional[str]:
    if not operator:
        return None
    op = _normalize_piko_operator(operator)
    if op == "DR":
        return _dr_country_from_era(era)
    mapping: dict[str, str] = {
        "DB": "DE",
        "DRG": "DE",
        "K.W.St.E.": "DE",
        "ÖBB": "AT",
        "SBB": "CH",
        "SBB Cargo": "CH",
        "BLS": "CH",
        "BLS Cargo": "CH",
        "RhB": "CH",
        "Rhätische Bahn": "CH",
        "PKP": "PL",
        "PKP Cargo": "PL",
        "CSD": "CS",
        "CD": "CZ",
        "ZSSK": "SK",
        "SNCB": "BE",
        "NS": "NL",
        "VSM": "NL",
        "SNCF": "FR",
        "FS": "IT",
        "GTS Rail": "IT",
        "Mercitalia Rail": "IT",
        "SBW": "AT",
        "MAV": "HU",
        "SJ": "SE",
        "DSB": "DK",
        "D&RGW": "US",
        "SP (Southern Pacific)": "US",
    }
    return mapping.get(op) or mapping.get(operator.strip())


def _description_has_installed_decoder(description: str) -> bool:
    """
    PIKO Gleichstrom: nur mit werkseitigem Decoder bzw. Sound-Variante als DC-Digital.
    DCC-Schnittstelle, nachrüstbarer Sound oder «mit PluX22 Decoder» bei Beleuchtung
    zählen nicht (das ist die DC-Analog-Stufe).
    """
    d = description or ""
    first = d.split("\n", 1)[0]
    if re.search(
        r"\bSound[\s-]*(E-|Diesel|E-Trieb|Trieb|Elektro|Zweikraft)",
        first,
        re.I,
    ):
        return True
    if "Sound ja/nein: ja" in d:
        return True
    if "Verbauter Decoder:" in d:
        return True
    if "Sound: PIKO Sound-Decoder werkseitig" in d:
        return True
    return False


def _canonical_electric_system_from_description(description: str) -> Optional[str]:
    """Richtung Locobox-Kanon: DC-/AC-Analog bzw. -Digital aus Shop-Beschreibung."""
    d = description or ""
    if "Stromsystem: Gleichstrom" in d:
        return "DC-Digital" if _description_has_installed_decoder(d) else "DC-Analog"
    if "Stromsystem: Wechselstrom" in d:
        digital = _description_has_installed_decoder(d) or "Digitale Schnittstelle:" in d
        return "AC-Digital" if digital else "AC-Analog"
    return None


def _int_mm(val: str) -> Optional[int]:
    m = re.search(r"(\d+)", val or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _long_product_description(html: str) -> str:
    """Längere Fliesstext-Beschreibung statt nur Shop-Marketing-``og:title``."""
    for pat in (
        r'<div[^>]+itemprop=["\']description["\'][^>]*>(.*?)</div>',
        r'class=["\'][^"\']*product--description[^"\']*["\'][^>]*>(.*?)</div>',
        r'class=["\'][^"\']*product-detail[^"\']*description[^"\']*["\'][^>]*>(.*?)</div>',
    ):
        m = re.search(pat, html, re.I | re.S)
        if m:
            t = _html_to_plain(m.group(1))
            if len(t) > 80:
                return swiss_text(t)
    return ""


def _apply_piko_type_fixup(article: dict[str, Any]) -> None:
    """Shop-Titel nach Import bereinigen (gleiche Logik wie ``autofix_piko_shop_type``)."""
    script = (
        Path(__file__).resolve().parents[2]
        / "agents"
        / "lok-numbering-article-review"
        / "scripts"
        / "autofix_piko_shop_type.py"
    )
    if not script.is_file():
        return
    spec = importlib.util.spec_from_file_location("autofix_piko_shop_type", script)
    if spec is None or spec.loader is None:
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fix = mod.propose_fix(article)
    if not fix:
        return
    _, new_t, new_n, new_liv, new_op = fix
    model = article["model"]
    model["type"] = new_t
    if new_n:
        model["number"] = new_n
    if new_liv and not model.get("livery"):
        model["livery"] = new_liv
    if new_op:
        model["operator"] = new_op


def _apply_attributes_to_model(attrs: dict[str, str]) -> dict[str, Any]:
    model: dict[str, Any] = {
        "country": None,
        "operator": None,
        "type": None,
        "number": None,
        "livery": None,
        "scale": "H0",
        "electricSystem": None,
        "decoderInterface": None,
        "era": None,
        "luepMm": None,
        "minRadiusMm": None,
    }

    era = attrs.get("Epoche", "").strip()
    if era:
        model["era"] = era

    raw_op = attrs.get("Bahnverwaltung", "").strip()
    op = _normalize_piko_operator(raw_op)
    if op:
        model["operator"] = op
        model["country"] = _operator_to_country(op, model.get("era"))

    dec = attrs.get("Digitale Schnittstelle", "").strip()
    if dec:
        model["decoderInterface"] = dec

    mr = (
        attrs.get("Mindestradius [mm]", "")
        or attrs.get("Mindestradius [mm]:", "")
        or attrs.get("Mindestradius", "")
    ).strip()
    if mr:
        model["minRadiusMm"] = _int_mm(mr)

    luep_next = False
    luep_mm: Optional[int] = None
    for key in list(attrs.keys()):
        kl = key.lower()
        if "maßbezeichnung" in kl or "massbezeichnung" in kl:
            v = attrs[key]
            if re.search(r"lüp|luep|puffer", v, re.I):
                luep_next = True
        elif re.match(r"^maß\s*\[mm\]", key, re.I) or re.match(r"^mass\s*\[mm\]", key, re.I):
            if luep_next:
                luep_mm = _int_mm(attrs[key])
            luep_next = False
    if luep_mm is not None:
        model["luepMm"] = luep_mm

    return model


def parse_html(
    html: str,
    *,
    canonical_url: str,
    article: str,
    image_override: Optional[str],
) -> dict[str, Any]:
    title = _meta_content(html, "og:title") or ""
    if not title.strip():
        m = re.search(r"<title>([^<]+)</title>", html, re.I)
        if m:
            title = html_lib.unescape(m.group(1).strip())
    desc_meta = _meta_content(html, "og:description") or _meta_content(html, "description") or ""
    body_long = _long_product_description(html)
    if image_override and str(image_override).strip():
        img = str(image_override).strip()
    else:
        img = (
            _product_main_image_url(html, canonical_url)
            or (_meta_content(html, "og:image") or "")
        )
    img = _abs_url(canonical_url, img)
    price = _price_amount(html, canonical_url)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    attrs = _parse_product_attributes_table(html)
    model = _apply_attributes_to_model(attrs)
    type_line = _product_type_line_from_html(html, title)
    if type_line:
        model["type"] = type_line

    if body_long:
        description = body_long
    elif desc_meta and len(desc_meta) > len(title) and "Webshop" not in desc_meta:
        description = swiss_text(desc_meta)
    else:
        parts = [swiss_text(desc_meta or title)]
        if attrs:
            lines = [f"{k}: {v}" for k, v in attrs.items() if k not in ("WEEE-Registrierungsnummer",)]
            if lines:
                parts.append("\n".join(lines[:18]))
        description = "\n\n".join(p for p in parts if p).strip()

    es = _canonical_electric_system_from_description(description)
    if es:
        model["electricSystem"] = es

    payload = {
        "schemaVersion": "1.0.0",
        "id": f"piko-{article}",
        "manufacturer": "PIKO",
        "articleNumber": article,
        "releaseDate": None,
        "uvp": {"amount": price, "currency": "EUR"},
        "model": model,
        "description": description,
        "categories": [],
        "tags": [],
        "source": {
            "url": canonical_url,
            "notes": "Daten von der Webseite, automatisch geupdated.",
            "imageUrl": img or None,
        },
        "updatedAt": now,
    }
    _apply_piko_type_fixup(payload)
    return payload


def _finalize_tags(
    existing_tags: list[Any],
    *,
    campaign_tag: Optional[str],
    replace_tags: Optional[list[str]],
) -> list[str]:
    """Kampagnen-Tag setzen; ``replace_tags`` durch ``campaign_tag`` ersetzen (Reihenfolge behalten)."""
    tags: list[str] = [t for t in existing_tags if isinstance(t, str) and t.strip()]
    ct = (campaign_tag or "").strip()
    replace = {t.strip() for t in (replace_tags or []) if isinstance(t, str) and t.strip()}
    if ct and replace:
        tags = [ct if t in replace else t for t in tags]
    if ct and ct not in tags:
        tags.append(ct)
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="PIKO Shop PDP-HTML → articles/piko JSON.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--html-file", type=Path, help="Gespeichertes PDP-HTML.")
    src.add_argument("--stdin", action="store_true", help="HTML von stdin lesen.")
    ap.add_argument("--canonical-url", required=True, help="Kanonische PDP-URL der Session.")
    ap.add_argument("--article", required=True, help="Artikelnummer (Ziffern).")
    ap.add_argument("--notes", default="Daten von der Webseite, automatisch geupdated.")
    ap.add_argument("--image-url", default=None, help="Bild-URL überschreiben (z. B. aus Netzwerk).")
    ap.add_argument("--write", action="store_true", help="Nach articles/piko/{nr}.json schreiben.")
    ap.add_argument(
        "--campaign-tag",
        metavar="SLUG",
        default=None,
        help="Nur mit --write: Slug zu tags hinzufügen (z. B. piko-neuheiten-2025).",
    )
    ap.add_argument(
        "--replace-tag",
        action="append",
        metavar="SLUG",
        default=None,
        help=(
            "Nur mit --write: vor --campaign-tag diese Slugs ersetzen "
            "(mehrfach oder kommagetrennt; z. B. piko-neuheiten-2026)."
        ),
    )
    ap.add_argument("--quiet", action="store_true", help="Weniger stdout bei --write.")
    args = ap.parse_args()
    if args.campaign_tag and not args.write:
        print("error: --campaign-tag nur mit --write.", file=sys.stderr)
        return 2
    if args.replace_tag and not args.write:
        print("error: --replace-tag nur mit --write.", file=sys.stderr)
        return 2

    if args.stdin:
        html = sys.stdin.read()
    else:
        p = args.html_file.expanduser().resolve()
        if not p.is_file():
            print(f"error: HTML fehlt: {p}", file=sys.stderr)
            return 2
        html = p.read_text(encoding="utf-8", errors="replace")

    data = parse_html(
        html,
        canonical_url=str(args.canonical_url).strip(),
        article=str(args.article).strip(),
        image_override=(str(args.image_url).strip() if args.image_url else None),
    )
    if args.notes:
        data["source"]["notes"] = str(args.notes)

    replace_tags: list[str] = []
    for chunk in args.replace_tag or []:
        replace_tags.extend(p.strip() for p in chunk.split(",") if p.strip())

    if args.write:
        out_dir = _DEFAULT_ARTICLES
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{args.article}.json"
        existing_tags: list[Any] = []
        if out_path.is_file():
            try:
                prev = json.loads(out_path.read_text(encoding="utf-8"))
                existing_tags = prev.get("tags") or []
            except (json.JSONDecodeError, OSError):
                existing_tags = []
        if args.campaign_tag or replace_tags:
            data["tags"] = _finalize_tags(
                existing_tags,
                campaign_tag=args.campaign_tag,
                replace_tags=replace_tags or None,
            )
        elif existing_tags:
            data["tags"] = list(existing_tags)
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.quiet:
            print(str(out_path))
        return 0

    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
