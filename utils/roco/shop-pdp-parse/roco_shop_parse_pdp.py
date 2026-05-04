#!/usr/bin/env python3
"""
Parse Roco Magento PDP HTML (Metas: og:* inkl. ``og:image`` → ``source.imageUrl``; fehlt die Meta, Hauptbild ``img.main-image`` / ``#img`` mit ``src`` oder ``data-src`` und PDP‑Basis‑URL absolutisieren; optional ``--image-url`` überschreibt die Bild-URL z. B. aus Chrome-Netzwerk). ``product:price:amount``; UVP sonst aus
``div.product-head-price`` sichtbar z. B. «277,90€», optional fehlend; Kurzbeschreibung
bevorzugt aus ``div.product-add-form-text``, sonst ``og:description``; Zusatz-Tabelle
``table#product-attribute-specs-table`` (**mehrere** Tabellen mit derselben ID: Allgemeine Daten, Elektrik, Abmessungen) mit ``td.col.data[data-th]``, z. B. Spur (z. B. «H0») → ``model.scale``, Stromsystem → ``model.electricSystem`` nur ``dc`` oder ``ac`` (z. B. «DC Analog» → ``dc``), Schnittstelle (Decoder/PluX, Freitext) → ``model.decoderInterface``, Bahngesellschaft → ``model.operator``, Epoche (z. B. «I») → ``model.era``, «Länge über Puffer» (LüP) → ``model.luepMm``, Mindestradius → ``model.minRadiusMm``).
Optional merge nach ``articles/roco/{articleNumber}.json``.

Es gibt **kein** HTTP-Laden im CLI: nur ``--html-file`` oder ``--stdin`` plus optional
``--canonical-url`` (PDP-URL aus der Browser-Session, kein GET).

For agents: nach gespeichertem PDP-HTML (Browser / MCP) dieses CLI nutzen.

Examples::

    python utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py --html-file /tmp/pdp.html --canonical-url 'https://www.roco.cc/.../70035-....html' --write

    cat /tmp/pdp.html | python utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py --stdin --canonical-url 'https://www.roco.cc/.../70035-....html' --write

Schweizer Textnormalisierung in Beschreibungen: «ß» → «ss» (kein Eszett).
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from urllib.parse import urljoin
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ARTICLES = _REPO_ROOT / "articles" / "roco"
_DEFAULT_NOTES = "Daten von der Webseite, automatisch geupdated."
# Roco ``og:title``: «Kategorie Typ/Betriebsnummer, Betreiber» (längste zuerst matchen).
_ROCO_TITLE_CATEGORY_PREFIXES: tuple[str, ...] = tuple(
    sorted(
        {
            "Nahverkehrs-Steuerwagen",
            "Elektrotriebzug",
            "Diesellokomotive",
            "Elektrolokomotive",
            "Dampflokomotive",
            "Personenwagen",
            "Güterwagen",
            "Packwagen",
            "Pufferwagen",
            "Speisewagen",
            "Schlafwagen",
            "Triebzug",
            "Steuerwagen",
            "Dampflok",
            "Elektrolok",
            "Diesellok",
        },
        key=len,
        reverse=True,
    )
)
_MERGE_ONLY_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "source.url",
        "source.notes",
        "source.imageUrl",
        "uvp",
        "description",
        "model",
    }
)
_ART_FROM_URL = re.compile(r"/(\d{5,8})-[^/]+\.html", re.IGNORECASE)
# Magento «Weitere Informationen»: data-th (de) → model-Feld
_SPEC_TO_MODEL_STR: dict[str, str] = {
    "Bahngesellschaft": "operator",
    "Epoche": "era",
    "Stromsystem": "electricSystem",
    "Schnittstelle": "decoderInterface",
}


def swiss_text(s: str) -> str:
    return s.replace("\u00df", "ss").replace("ß", "ss")


def _trim_ws(s: str) -> str:
    """Führende und nachfolgende Leerzeichen entfernen, Folgen von Whitespace zu einem Leerzeichen."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", swiss_text(str(s).strip())).strip()


def _trim_description_merge(s: str) -> str:
    """
    Rand trimmen, Zeilenumbrüche beibehalten; pro Zeile nur Spaces/Tabs zusammenziehen
    (kein ``\\n`` → Leerzeichen wie bei ``_trim_ws``).
    """
    t = swiss_text(str(s).strip())
    if not t:
        return ""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in t.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _meta_prop(html: str, prop: str) -> Optional[str]:
    esc = re.escape(prop)
    patterns = (
        rf'<meta\s+property="{esc}"\s+content="([^"]*)"',
        rf"<meta\s+property=['\"]{esc}['\"]\s+content=['\"]([^'\"]*)['\"]",
        rf'<meta\s+content="([^"]*)"\s+property="{esc}"',
        rf"<meta\s+content=['\"]([^'\"]*)['\"]\s+property=['\"]{esc}['\"]",
    )
    for pat in patterns:
        m = re.search(pat, html, re.I | re.DOTALL)
        if m:
            return html_lib.unescape(m.group(1)).replace("&#x20;", " ").strip()
    return None


def _absolute_url(href: str, base: str) -> str:
    href = html_lib.unescape(href).strip()
    if not href:
        return href
    if href.startswith(("http://", "https://", "//")):
        return href
    b = (base or "").strip()
    if not b:
        return href
    return urljoin(b, href)


def _product_image_url(html: str, base_url: str) -> Optional[str]:
    """
    Produktbild: ``og:image``, sonst ``twitter:image``, sonst Galerie
    ``img#img`` / ``img.main-image`` (``src`` oder ``data-src``, oft ``/responsebinary.php?…``).
    Relative ``src`` mit ``base_url`` (kanonische PDP‑URL) absolutisieren.
    """
    u = _meta_prop(html, "og:image")
    if u:
        return u.strip() or None
    m = re.search(
        r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']*)["\']',
        html,
        re.I,
    )
    if m:
        t = html_lib.unescape(m.group(1)).strip()
        if t:
            return t
    base = (base_url or "").strip() or _meta_prop(html, "og:url") or ""
    for pat in (
        r'<img\b[^>]*\bid=["\']img["\'][^>]*\bclass=["\'][^"\']*main-image[^"\']*["\'][^>]*\b(?:src|data-src)=["\']([^"\']+)["\']',
        r'<img\b[^>]*\bclass=["\'][^"\']*main-image[^"\']*["\'][^>]*\bid=["\']img["\'][^>]*\b(?:src|data-src)=["\']([^"\']+)["\']',
        r'<img\b[^>]*\bclass=["\'][^"\']*main-image[^"\']*["\'][^>]*\b(?:src|data-src)=["\']([^"\']+)["\']',
        r'<img\b[^>]*\bid=["\']img["\'][^>]*\b(?:src|data-src)=["\']([^"\']+)["\']',
    ):
        mm = re.search(pat, html, re.I | re.DOTALL)
        if mm:
            src = _absolute_url(mm.group(1), base)
            if src:
                return src
    return None


def _normalize_desc(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    t = re.sub(r"\s+", " ", raw).strip()
    t = t.replace("■", ". ").replace("·", ". ")
    t = re.sub(r"\s*\.\s*\.\s*", ". ", t)
    t = swiss_text(t)
    return t.strip()


def _extract_inner_html_of_div_with_class(
    html: str, class_token: str
) -> Optional[str]:
    """
    Inneres HTML des ersten ``<div class="… class_token …">`` bis zum zugehörigen
    schliessenden ``</div>`` (verschachtelte ``<div>`` werden mitgezählt).
    """
    pos = 0
    opener = re.compile(
        r'<div\b[^>]*\bclass\s*=\s*["\']([^"\']*)["\'][^>]*>',
        re.I,
    )
    while True:
        m = opener.search(html, pos)
        if not m:
            return None
        class_attr = m.group(1)
        parts = class_attr.split()
        if class_token not in parts:
            pos = m.end()
            continue
        start = m.end()
        depth = 1
        scan = start
        while depth > 0 and scan < len(html):
            next_open = html.find("<div", scan)
            next_close = html.find("</div>", scan)
            if next_close < 0:
                return None
            if 0 <= next_open < next_close:
                depth += 1
                scan = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    return html[start:next_close]
                scan = next_close + 6
        pos = m.start() + 1


def _extract_product_add_form_text(html: str) -> Optional[str]:
    """Sichtbarer Kurztext unter ``product-add-form-text`` (Kurzbeschreibung PDP)."""
    inner = _extract_inner_html_of_div_with_class(html, "product-add-form-text")
    if not inner:
        return None
    raw = html_lib.unescape(_strip_html_tags(inner))
    raw = raw.replace("\xa0", " ").replace("&nbsp;", " ")
    raw = re.sub(r"\s+", " ", raw).strip()
    return _normalize_desc(raw)


def _price_amount(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _parse_visible_euro_price(raw: str) -> Optional[float]:
    """
    Preis aus sichtbarem Text (z. B. «277,90 €», «1.234,56€»). Währungszeichen
    und Leerzeichen werden ignoriert. Deutsch: Tausenderpunkt, Dezimalkomma.
    """
    if not raw:
        return None
    t = html_lib.unescape(raw)
    t = t.replace("\xa0", " ").replace("&nbsp;", " ")
    t = re.sub(r"\s+", "", t.strip())
    t = re.sub(r"[€$]", "", t, flags=re.I)
    t = t.replace("EUR", "").replace("CHF", "")
    if not t:
        return None
    if re.search(r",\d{1,2}$", t):
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    if not m:
        return None
    return _price_amount(m.group(1))


def _extract_product_head_price_amount(html: str) -> Optional[float]:
    """UVP aus ``div.product-head-price``, falls der Meta-Preis fehlt."""
    inner = _extract_inner_html_of_div_with_class(html, "product-head-price")
    if not inner:
        return None
    visible = _strip_html_tags(inner)
    return _parse_visible_euro_price(visible)


def _strip_html_tags(fragment: str) -> str:
    return re.sub(r"<[^>]+>", " ", fragment)


def _td_class_has_col_and_data(attrs: str) -> bool:
    """
    Magento schreibt meist ``col data``, selten andere Reihenfolge; Zeilen mit
    ``col label`` ignorieren (kein Wort ``data`` als Klassen-Token).
    """
    m = re.search(r'\bclass\s*=\s*["\']([^"\']*)["\']', attrs, re.I)
    if not m:
        return False
    parts = {p.lower() for p in re.split(r"\s+", m.group(1).strip()) if p}
    return "col" in parts and "data" in parts


def _specs_label_is_min_radius(label: str) -> bool:
    """Roco/Magento: «Mindestradius», «Mindest-Radius», Leerzeichenvarianten."""
    n = re.sub(r"\s+", " ", (label or "").strip()).lower()
    n = n.replace("–", "-").replace("—", "-")
    return "mindest" in n and "radius" in n


def _specs_raw_mindestradius(specs: dict[str, str]) -> Optional[str]:
    v = specs.get("Mindestradius")
    if v and str(v).strip():
        return str(v).strip()
    for key, val in specs.items():
        if not val or not str(val).strip():
            continue
        if _specs_label_is_min_radius(key):
            return str(val).strip()
    return None


def _fuzzy_min_radius_cell_from_html(html: str) -> Optional[str]:
    """Letzter Fallback: col+data-Zelle, deren ``data-th`` wie Mindestradius aussieht."""
    for cell in re.finditer(r"<td([^>]*)>([\s\S]*?)</td>", html, re.I):
        attrs, inner = cell.group(1), cell.group(2)
        if not _td_class_has_col_and_data(attrs):
            continue
        dm = re.search(r'\bdata-th\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
        if not dm:
            continue
        label = html_lib.unescape(dm.group(1)).strip()
        if not _specs_label_is_min_radius(label):
            continue
        text = html_lib.unescape(_strip_html_tags(inner))
        text = text.replace("\xa0", " ").replace("&nbsp;", " ")
        text = swiss_text(re.sub(r"\s+", " ", text).strip())
        if text:
            return text
    return None


def _specs_td_value_by_data_th(html: str, th_label: str) -> Optional[str]:
    """
    Fallback: einzelne Wert-Zelle per ``data-th`` im ganzen Dokument (wenn die
    Tabellen-Zerlegung wegen Zeilenumbrüchen im ``<table``-Tag o. Ä. lückenhaft ist).
    """
    esc = re.escape(th_label)
    m = re.search(
        rf'<td[^>]*\bdata-th\s*=\s*["\']{esc}["\'][^>]*>([\s\S]*?)</td>',
        html,
        re.I,
    )
    if not m:
        return None
    text = html_lib.unescape(_strip_html_tags(m.group(1)))
    text = text.replace("\xa0", " ").replace("&nbsp;", " ")
    text = swiss_text(re.sub(r"\s+", " ", text).strip())
    return text or None


def _extract_specs_table(html: str) -> dict[str, str]:
    """
    Liest **alle** ``table#product-attribute-specs-table``-Blöcke. Roco Magento
    wiederholt dieselbe ID pro Sektion (Allgemeine Daten, Elektrik, Abmessungen);
    LüP steht oft nur in der letzten. Öffnungs-``<table>`` kann mehrzeilig sein
    (``[^>]*`` würde dort abbrechen). Wert-Zellen: ``td`` mit Klassen ``col`` und
    ``data`` sowie ``data-th``.
    """
    out: dict[str, str] = {}
    table_block = re.compile(
        r'<table[\s\S]*?\bid\s*=\s*["\']product-attribute-specs-table["\'][\s\S]*?>'
        r"([\s\S]*?)</table>",
        re.I,
    )
    for m in table_block.finditer(html):
        block = m.group(1)
        for cell in re.finditer(r"<td([^>]*)>(.*?)</td>", block, re.I | re.DOTALL):
            attrs, inner = cell.group(1), cell.group(2)
            if not _td_class_has_col_and_data(attrs):
                continue
            dm = re.search(r'\bdata-th\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
            if not dm:
                continue
            label = html_lib.unescape(dm.group(1)).strip()
            text = html_lib.unescape(_strip_html_tags(inner))
            text = text.replace("\xa0", " ").replace("&nbsp;", " ")
            text = swiss_text(re.sub(r"\s+", " ", text).strip())
            if label and text:
                out[label] = text
    for th_key in ("Länge über Puffer", "Mindestradius"):
        if th_key not in out:
            fb = _specs_td_value_by_data_th(html, th_key)
            if fb:
                out[th_key] = fb
    if "Mindestradius" not in out:
        fz = _fuzzy_min_radius_cell_from_html(html)
        if fz:
            out["Mindestradius"] = fz
    return out


def _parse_mm_int(raw: str) -> Optional[int]:
    """
    Erste Massangabe in mm aus PDP-Text («101 mm», «358,5 mm»), gerundet auf ganze mm.
    """
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*mm\b", raw, re.I)
    if not m:
        m = re.search(r"(\d+(?:[.,]\d+)?)", raw)
    if not m:
        return None
    try:
        num = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    return int(round(num))


def _parse_min_radius_mm(raw: str) -> Optional[int]:
    """Mindestradius in mm (gleiche Logik wie LüP)."""
    return _parse_mm_int(raw)


def _normalize_spur_scale(raw: str) -> Optional[str]:
    """
    Spur-Bezeichnung wie im Shop (z. B. «H0», «TT», «N») auf Kleinbuchstaben ohne
    Leerzeichen, konsistent zu ``articles/roco/*.json`` (typisch ``h0``).
    Verwechslung lateinisches «O» vs. Ziffer «0» bei H0: «ho» → «h0``.
    An Markup-/Export-Artefakten: angeklebte Attributsnamen («Epoche», «Spur») entfernen.
    """
    t = swiss_text(raw.strip())
    t = re.sub(r"(?i)(epoche|spurweite|massstab|spur)$", "", t)
    t = re.sub(r"(?i)^(epoche|spurweite|massstab|spur)", "", t)
    t = re.sub(r"\s+", "", t).lower()
    if not t:
        return None
    m = re.search(r"(?i)^(h0|ho|tt|n|z|g)(?![a-z0-9])", t)
    if m:
        chunk = m.group(1).lower()
        if chunk in ("h0", "ho"):
            return "h0"
        return chunk
    if re.fullmatch(r"h[o0]", t):
        return "h0"
    return t if len(t) <= 12 else None


def _sanitize_epoche_value(text: str) -> str:
    """
    Epoche oft «I», «III-IV»; bei fehlerhaft zusammengezogenem Text nur den Epoche‑Teil
    (z. B. «I Bahngesellschaft» → «I»).
    """
    t = swiss_text(text.strip())
    m = re.match(r"^\s*([IVX]+(?:-[IVX]+)?)\b", t, re.I)
    if m:
        return m.group(1).upper()
    parts = t.split()
    if parts and len(parts[0]) <= 6 and re.fullmatch(r"[IVX]+(?:-[IVX]+)?", parts[0], re.I):
        return parts[0].upper()
    return parts[0] if parts else t


def _sanitize_operator_value(text: str) -> str:
    t = swiss_text(text.strip())
    t = re.sub(r"(?i)^bahngesellschaft\s+", "", t)
    return t.strip()


def _normalize_electric_system(raw: str) -> Optional[str]:
    """
    Nur ``dc`` oder ``ac`` (Kleinbuchstaben). Roco-Texte wie «DC Analog», «DCC»,
    «Wechselstrom» werden zugeordnet; unklarer Text → ``None``.
    """
    if not raw or not str(raw).strip():
        return None
    t = swiss_text(str(raw).strip()).upper()
    t = re.sub(r"\s+", " ", t)
    if re.search(r"\bAC\b", t) or "WECHSELSTROM" in t:
        return "ac"
    if (
        re.search(r"\bDC\b", t)
        or "DCC" in t
        or "GLEICHSTROM" in t
        or "DIGITAL" in t
        or "ANALOG" in t
    ):
        return "dc"
    return None


def _specs_to_model_patch(specs: dict[str, str]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for de_label, model_key in _SPEC_TO_MODEL_STR.items():
        val = specs.get(de_label)
        if not val or not str(val).strip():
            continue
        val = _trim_ws(str(val))
        if not val:
            continue
        if model_key == "era":
            val = _sanitize_epoche_value(val)
            if val:
                patch[model_key] = _trim_ws(val)
        elif model_key == "operator":
            val = _sanitize_operator_value(val)
            if val:
                patch[model_key] = _trim_ws(val)
        elif model_key == "electricSystem":
            patch[model_key] = _normalize_electric_system(val)
        else:
            patch[model_key] = val
    spur = specs.get("Spur")
    if spur:
        sc = _normalize_spur_scale(spur)
        if sc:
            patch["scale"] = sc
    luep_raw = specs.get("Länge über Puffer")
    if luep_raw:
        luep = _parse_mm_int(luep_raw)
        if luep is not None:
            patch["luepMm"] = luep
    min_raw = _specs_raw_mindestradius(specs)
    if min_raw:
        mm = _parse_min_radius_mm(min_raw)
        if mm is not None:
            patch["minRadiusMm"] = mm
    return patch


def _strip_leading_roco_title_sku(head: str) -> str:
    """
    Roco setzt in ``og:title`` oft die Artikelnummer vor die Kategorie
    (z. B. «7500178 Elektrolokomotive 145 070-9, RBH»). Wiederholt 5–8 Ziffern + Leerzeichen am Anfang entfernen.
    """
    h = _trim_ws(head)
    if not h:
        return h
    while True:
        nxt = re.sub(r"^\d{5,8}\s+", "", h, count=1)
        if nxt == h:
            break
        h = _trim_ws(nxt)
    return h


def _category_slug_from_roco_title_prefix(prefix: str) -> str:
    """Kategorie-Wort aus dem Titel → Slug (ASCII, Bindestriche)."""
    s = swiss_text(prefix.strip().lower())
    for u, rep in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("é", "e")):
        s = s.replace(u, rep)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "roco"


def _parse_roco_og_title(title: Optional[str]) -> tuple[dict[str, Any], list[str]]:
    """
    Roco ``og:title``: optional führende Artikelnummer(n), dann «Kategorie Typ/Betriebsnummer, Betreiber».
    Liefert ``type`` = Typ/Betriebsnummer (ein Feld), ``number`` = ``None``,
    ``operator`` = Text ab dem **ersten** Komma (kann weitere Kommata enthalten).
    Der Typ-Teil vor diesem Komma darf **kein** Komma enthalten, sonst schlägt die Zuordnung fehl.
    Plus Kategorie-Slug für ``categories``.
    """
    if not title or not str(title).strip():
        return {}, []
    t = _trim_ws(str(title))
    if "," not in t:
        return {}, []
    head, op_raw = t.split(",", 1)
    head = _strip_leading_roco_title_sku(head)
    op = _trim_ws(op_raw)
    if not head or not op:
        return {}, []
    matched: Optional[str] = None
    type_part = ""
    for pref in _ROCO_TITLE_CATEGORY_PREFIXES:
        if head.startswith(pref + " "):
            matched = pref
            type_part = _trim_ws(head[len(pref) + 1 :])
            break
    if not matched or not type_part:
        return {}, []
    slug = _trim_ws(_category_slug_from_roco_title_prefix(matched))
    return (
        {"type": type_part, "number": None, "operator": op},
        [slug] if slug else [],
    )


def _should_apply_title_derived(merge_only: Optional[set[str]]) -> bool:
    """Titel-Ableitung nur bei vollem Merge, nicht bei reinem ``--merge-config``-Spez-Subset."""
    if merge_only is None:
        return True
    keys = {"model.type", "model.number", "model.operator"}
    return bool(keys & merge_only)


def parse_pdp(html: str, fallback_url: Optional[str] = None) -> dict[str, Any]:
    canon = _meta_prop(html, "og:url") or fallback_url or ""
    title = _meta_prop(html, "og:title")
    desc_pdp = _extract_product_add_form_text(html)
    desc_og = _normalize_desc(_meta_prop(html, "og:description"))
    desc = desc_pdp if desc_pdp else desc_og
    price = _price_amount(_meta_prop(html, "product:price:amount"))
    if price is None:
        price = _extract_product_head_price_amount(html)

    article: Optional[str] = None
    if canon:
        m = _ART_FROM_URL.search(canon)
        if m:
            article = m.group(1)
    if article is None and fallback_url:
        m = _ART_FROM_URL.search(fallback_url)
        if m:
            article = m.group(1)

    specs = _extract_specs_table(html)
    model_patch = _specs_to_model_patch(specs)
    title_model, title_cats = _parse_roco_og_title(title)
    canon_clean = canon.strip().split("#")[0].strip() if canon else ""
    image_url = _product_image_url(html, canon_clean)

    return {
        "articleNumber": article,
        "canonicalUrl": canon_clean or None,
        "title": _trim_ws(title) if title and str(title).strip() else None,
        "description": desc,
        "uvpAmount": price,
        "currency": "EUR",
        "imageUrl": image_url,
        "specsRaw": specs,
        "modelPatch": model_patch,
        "titleModelPatch": title_model,
        "titleCategorySlugs": title_cats,
    }


def _utc_stamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_merge_only_args(chunks: Optional[list[str]]) -> Optional[set[str]]:
    """
    CLI: mehrere ``--merge-only "a,b"`` oder ein Argument mit Kommas.
    ``None`` = alle Merge-Ziele (Standard).
    """
    if not chunks:
        return None
    out: set[str] = set()
    for chunk in chunks:
        for part in re.split(r"[\s,]+", chunk.strip()):
            if part:
                out.add(part)
    return out or None


def _validate_merge_only(keys: set[str]) -> None:
    for k in keys:
        if k in _MERGE_ONLY_TOP_LEVEL:
            continue
        if k.startswith("model.") and len(k) > len("model."):
            continue
        allowed = ", ".join(sorted(_MERGE_ONLY_TOP_LEVEL))
        raise SystemExit(
            f"error: unbekannter --merge-only Schlüssel «{k}». "
            f"Erlaubt: {allowed}, model.<feldname> (z. B. model.luepMm)"
        )


def _merge_only_from_config_file(path: Path) -> set[str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise SystemExit(f"error: merge-config nicht lesbar: {e}") from e
    except json.JSONDecodeError as e:
        raise SystemExit(f"error: merge-config kein gültiges JSON: {e}") from e
    keys = raw.get("mergeOnly") or raw.get("merge_only")
    if keys is None:
        raise SystemExit(
            "error: merge-config braucht Top-Level-Liste «mergeOnly» oder «merge_only»."
        )
    if not isinstance(keys, list):
        raise SystemExit("error: mergeOnly / merge_only muss eine JSON-Liste sein.")
    out = {str(x).strip() for x in keys if str(x).strip()}
    if not out:
        raise SystemExit("error: mergeOnly / merge_only ist leer.")
    return out


def _model_skeleton() -> dict[str, Any]:
    return {
        "country": None,
        "operator": None,
        "type": None,
        "number": None,
        "livery": None,
        "scale": "h0",
        "electricSystem": None,
        "decoderInterface": None,
        "era": None,
        "luepMm": None,
        "minRadiusMm": None,
    }


def _article_skeleton(article: str) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "id": f"roco-{article}",
        "manufacturer": "Roco",
        "articleNumber": article,
        "releaseDate": None,
        "uvp": {"amount": None, "currency": "EUR"},
        "model": _model_skeleton(),
        "description": "",
        "categories": ["lokomotive"],
        "tags": ["h0"],
        "source": {
            "url": "https://www.roco.cc/",
            "notes": "",
            "imageUrl": None,
        },
        "updatedAt": _utc_stamp(),
    }


def article_record_stub(article_number: str) -> dict[str, Any]:
    """Minimaler Roco-Artikel-Datensatz (Platzhalter), gleiche Struktur wie ``_article_skeleton``."""
    art = str(article_number).strip()
    if not art.isdigit() or not (5 <= len(art) <= 8):
        raise ValueError(
            f"Artikelnummer muss 5–8 Ziffern sein, ungültig: {article_number!r}"
        )
    return _article_skeleton(art)


def merge_article_record(
    parsed: dict[str, Any],
    *,
    notes: str,
    articles_root: Path,
    article_override: Optional[str],
    merge_only: Optional[set[str]] = None,
) -> tuple[dict[str, Any], Path]:
    art = article_override or parsed.get("articleNumber")
    if not art:
        raise SystemExit(
            "error: Artikelnummer nicht ermittelt (og:url prüfen oder --article setzen)."
        )

    path = articles_root / f"{art}.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SystemExit(
                f"error: bestehende Datei ist kein gültiges JSON: {path}\n{e}"
            ) from e
        except OSError as e:
            raise SystemExit(f"error: Datei nicht lesbar: {path}\n{e}") from e
    else:
        data = _article_skeleton(art)

    src_old = data.get("source")
    if isinstance(src_old, dict):
        src_old.pop("headInfoBadges", None)
        src_old.pop("headInfoIconsText", None)

    def allow(field: str) -> bool:
        return merge_only is None or field in merge_only

    canon = parsed.get("canonicalUrl") or ""
    if canon and allow("source.url"):
        data.setdefault("source", {})
        data["source"]["url"] = str(canon).strip()
    if allow("source.notes"):
        data.setdefault("source", {})
        data["source"]["notes"] = notes.strip() if isinstance(notes, str) else notes

    if allow("source.imageUrl"):
        img = parsed.get("imageUrl")
        if isinstance(img, str) and img.strip():
            data.setdefault("source", {})
            data["source"]["imageUrl"] = img.strip()
        else:
            src = data.get("source")
            if isinstance(src, dict) and "imageUrl" in src:
                del src["imageUrl"]

    if parsed.get("uvpAmount") is not None and allow("uvp"):
        data.setdefault("uvp", {})
        data["uvp"]["amount"] = parsed["uvpAmount"]
        data["uvp"]["currency"] = parsed.get("currency") or "EUR"

    if parsed.get("description") and allow("description"):
        d = parsed["description"]
        data["description"] = _trim_description_merge(d) if isinstance(d, str) else d

    mp = parsed.get("modelPatch") or {}
    if isinstance(mp, dict) and mp:
        model_all = merge_only is None or "model" in merge_only
        data.setdefault("model", _model_skeleton())
        for k, v in mp.items():
            if merge_only is not None and not model_all and f"model.{k}" not in merge_only:
                continue
            if k == "electricSystem":
                if v is None:
                    data["model"][k] = None
                elif isinstance(v, str) and v.strip():
                    data["model"][k] = _normalize_electric_system(v)
                continue
            if isinstance(v, str):
                tv = _trim_ws(v)
                if tv:
                    data["model"][k] = tv
            elif v is not None:
                data["model"][k] = v

    tp = parsed.get("titleModelPatch") or {}
    tc = parsed.get("titleCategorySlugs") or []
    if isinstance(tp, dict) and tp and _should_apply_title_derived(merge_only):
        data.setdefault("model", _model_skeleton())
        model_all = merge_only is None or "model" in merge_only
        for k in ("type", "number", "operator"):
            if k not in tp:
                continue
            if merge_only is not None and not model_all and f"model.{k}" not in merge_only:
                continue
            v = tp[k]
            if v is None:
                data["model"][k] = None
            elif isinstance(v, str):
                tv = _trim_ws(v)
                data["model"][k] = tv if tv else None
            else:
                data["model"][k] = v
    if (
        isinstance(tc, list)
        and tc
        and merge_only is None
    ):
        cats = list(data.get("categories") or [])
        seen = set(cats)
        for c in tc:
            if not isinstance(c, str):
                continue
            cs = _trim_ws(c)
            if cs and cs not in seen:
                cats.append(cs)
                seen.add(cs)
        data["categories"] = cats

    data["updatedAt"] = _utc_stamp()
    return data, path


def _load_html_source(args: argparse.Namespace) -> tuple[str, Optional[str]]:
    canon = getattr(args, "canonical_url", None) or None
    if args.stdin:
        return sys.stdin.read(), canon
    if args.html_file:
        p = args.html_file.expanduser().resolve()
        return p.read_text(encoding="utf-8", errors="replace"), canon
    raise SystemExit("error: eine Quelle angeben: --html-file oder --stdin.")


def _print_json_line(obj: Any) -> None:
    try:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except OSError:
            pass
        raise SystemExit(0)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Roco PDP HTML parsen und optional articles/roco/*.json mergen.",
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--html-file",
        type=Path,
        metavar="PATH",
        help="Lokale HTML-Datei.",
    )
    src.add_argument(
        "--stdin",
        action="store_true",
        help="HTML von stdin lesen.",
    )
    ap.add_argument(
        "--canonical-url",
        metavar="URL",
        help="Nur mit --html-file/--stdin: PDP-URL als Fallback für og:url, source.url und Artikelnummer (kein HTTP).",
    )
    ap.add_argument(
        "--article",
        metavar="NR",
        help="Artikelnummer erzwingen, falls URL-Parsing scheitert.",
    )
    ap.add_argument(
        "--image-url",
        metavar="URL",
        default=None,
        help="Produktbild-URL erzwingen (z. B. aus Chrome-Netzwerk), überschreibt HTML-Parsing für source.imageUrl.",
    )
    ap.add_argument(
        "--articles-root",
        type=Path,
        default=_DEFAULT_ARTICLES,
        help=f"Zielverzeichnis für --write (default: {_DEFAULT_ARTICLES}).",
    )
    ap.add_argument(
        "--notes",
        default=_DEFAULT_NOTES,
        help=f'source.notes (default: «{_DEFAULT_NOTES}»).',
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help="JSON nach articles-root/{article}.json schreiben.",
    )
    ap.add_argument(
        "--merge-only",
        action="append",
        metavar="KEYS",
        help=(
            "Nur mit --write: nur diese Ziele aus dem Parse überschreiben (Komma- oder "
            "Leerzeichen-getrennt; Argument mehrfach erlaubt). Standard ohne diese Option: alles wie bisher. "
            "Schlüssel: source.url, source.notes, source.imageUrl, uvp, description, model "
            "(gesamtes modelPatch), model.FELD (z. B. model.luepMm, model.minRadiusMm, model.electricSystem). "
            "Vorgefülltes Preset (nur Spec-Tabelle / Abmessungen): "
            "utils/roco/shop-pdp-parse/merge-pdp-specs-fields.json. "
            "Zusammen mit --merge-config werden die Mengen vereinigt."
        ),
    )
    ap.add_argument(
        "--merge-config",
        type=Path,
        metavar="PATH",
        help=(
            "Nur mit --write: JSON-Datei mit «mergeOnly» oder «merge_only» (Liste von Schlüsseln, "
            "gleiche Namen wie bei --merge-only). Wird mit --merge-only vereinigt. "
            "Preset siehe --merge-only Hilfetext."
        ),
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Keine JSON-Ausgabe auf stdout (nur mit --write sinnvoll).",
    )
    args = ap.parse_args()
    if args.canonical_url and not (args.html_file or args.stdin):
        raise SystemExit(
            "error: --canonical-url nur zusammen mit --html-file oder --stdin."
        )

    try:
        html, fallback_url = _load_html_source(args)
    except OSError as e:
        print(f"error: Eingabe nicht lesbar: {e}", file=sys.stderr)
        return 1

    parsed = parse_pdp(html, fallback_url=fallback_url)
    if args.article:
        parsed["articleNumber"] = args.article
    if args.image_url and str(args.image_url).strip():
        parsed["imageUrl"] = str(args.image_url).strip()

    articles_root = args.articles_root.expanduser().resolve()

    if args.write:
        merge_only = _parse_merge_only_args(args.merge_only)
        if args.merge_config:
            cfg = _merge_only_from_config_file(
                args.merge_config.expanduser().resolve()
            )
            merge_only = cfg if merge_only is None else (merge_only | cfg)
        if merge_only is not None:
            _validate_merge_only(merge_only)
        merged, path = merge_article_record(
            parsed,
            notes=args.notes,
            articles_root=articles_root,
            article_override=args.article,
            merge_only=merge_only,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path}", file=sys.stderr)
        if not args.quiet:
            _print_json_line(merged)
    elif not args.quiet:
        _print_json_line(parsed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
