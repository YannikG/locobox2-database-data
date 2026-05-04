#!/usr/bin/env python3
"""
Parse Roco Magento PDP HTML (Metas: og:* inkl. ``og:image`` → ``source.imageUrl``; fehlt die Meta, Hauptbild ``img.main-image`` / ``#img`` mit ``src`` oder ``data-src`` und PDP‑Basis‑URL absolutisieren; optional ``--image-url`` überschreibt die Bild-URL z. B. aus Chrome-Netzwerk). ``product:price:amount``; UVP sonst aus
``div.product-head-price`` sichtbar z. B. «277,90€», optional fehlend; Kurzbeschreibung
bevorzugt aus ``div.product-add-form-text``, sonst ``og:description``; Zusatz-Tabelle
``#product-attribute-specs-table`` mit ``td[data-th]``, z. B. Spur (z. B. «H0») → ``model.scale``, Stromsystem → ``model.electricSystem`` nur ``dc`` oder ``ac`` (z. B. «DC Analog» → ``dc``), Schnittstelle (Decoder/PluX, Freitext) → ``model.decoderInterface``, Bahngesellschaft → ``model.operator``, Epoche (z. B. «I») → ``model.era``, «Länge über Puffer» (LüP) → ``model.luepMm``, Mindestradius → ``model.minRadiusMm``).
Optional merge nach ``articles/roco/{articleNumber}.json``.

For agents: avoid ad-hoc inline Python; use this CLI after you have either a PDP
URL (from browser «Page URL» metadata) or a saved HTML file.

Examples::

    python utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py --url 'https://www.roco.cc/.../70035-....html' --write

    python utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py --html-file /tmp/pdp.html --canonical-url 'https://www.roco.cc/.../70035-....html' --write

    curl -sSL -A 'Mozilla/5.0' 'URL' | python utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py --stdin --write

Schweizer Textnormalisierung in Beschreibungen: «ß» → «ss» (kein Eszett).
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ARTICLES = _REPO_ROOT / "articles" / "roco"
_DEFAULT_NOTES = "Daten von der Webseite, automatisch geupdated."
_USER_AGENT = "Mozilla/5.0 (compatible; locobox-roco-parse/1.0)"
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


def _extract_specs_table(html: str) -> dict[str, str]:
    """
    Liest ``table#product-attribute-specs-table``: Wert-Zellen
    ``<td class="col data" data-th="…">`` (Attributreihenfolge egal).
    """
    m = re.search(
        r'<table[^>]*\bid\s*=\s*["\']product-attribute-specs-table["\'][^>]*>(.*?)</table>',
        html,
        re.I | re.DOTALL,
    )
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, str] = {}
    for cell in re.finditer(r"<td([^>]*)>(.*?)</td>", block, re.I | re.DOTALL):
        attrs, inner = cell.group(1), cell.group(2)
        if not re.search(
            r'\bclass\s*=\s*["\'][^"\']*\bcol\s+data\b',
            attrs,
            re.I,
        ):
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
        if not val:
            continue
        if model_key == "era":
            val = _sanitize_epoche_value(val)
            if val:
                patch[model_key] = val
        elif model_key == "operator":
            val = _sanitize_operator_value(val)
            if val:
                patch[model_key] = val
        elif model_key == "electricSystem":
            patch[model_key] = _normalize_electric_system(val)
        elif val:
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
    min_raw = specs.get("Mindestradius")
    if min_raw:
        mm = _parse_min_radius_mm(min_raw)
        if mm is not None:
            patch["minRadiusMm"] = mm
    return patch


def fetch_html(url: str, timeout: float = 45.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        body = resp.read()
    return body.decode("utf-8", errors="replace")


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
    canon_clean = canon.split("#")[0] if canon else ""
    image_url = _product_image_url(html, canon_clean)

    return {
        "articleNumber": article,
        "canonicalUrl": canon.split("#")[0] if canon else None,
        "title": swiss_text(title) if title else None,
        "description": desc,
        "uvpAmount": price,
        "currency": "EUR",
        "imageUrl": image_url,
        "specsRaw": specs,
        "modelPatch": model_patch,
    }


def _utc_stamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


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
        "source": {"url": "", "notes": "", "imageUrl": None},
        "updatedAt": _utc_stamp(),
    }


def merge_article_record(
    parsed: dict[str, Any],
    *,
    notes: str,
    articles_root: Path,
    article_override: Optional[str],
) -> tuple[dict[str, Any], Path]:
    art = article_override or parsed.get("articleNumber")
    if not art:
        raise SystemExit(
            "error: Artikelnummer nicht ermittelt (og:url prüfen oder --article setzen)."
        )

    path = articles_root / f"{art}.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = _article_skeleton(art)

    src_old = data.get("source")
    if isinstance(src_old, dict):
        src_old.pop("headInfoBadges", None)
        src_old.pop("headInfoIconsText", None)

    canon = parsed.get("canonicalUrl") or ""
    if canon:
        data.setdefault("source", {})
        data["source"]["url"] = canon
    data.setdefault("source", {})
    data["source"]["notes"] = notes

    img = parsed.get("imageUrl")
    if isinstance(img, str) and img.strip():
        data.setdefault("source", {})
        data["source"]["imageUrl"] = img.strip()
    else:
        src = data.get("source")
        if isinstance(src, dict) and "imageUrl" in src:
            del src["imageUrl"]

    if parsed.get("uvpAmount") is not None:
        data.setdefault("uvp", {})
        data["uvp"]["amount"] = parsed["uvpAmount"]
        data["uvp"]["currency"] = parsed.get("currency") or "EUR"

    if parsed.get("description"):
        data["description"] = parsed["description"]

    mp = parsed.get("modelPatch") or {}
    if isinstance(mp, dict) and mp:
        data.setdefault("model", _model_skeleton())
        for k, v in mp.items():
            if k == "electricSystem":
                if v is None:
                    data["model"][k] = None
                elif str(v).strip():
                    data["model"][k] = v
                continue
            if v is not None and str(v).strip():
                data["model"][k] = v

    data["updatedAt"] = _utc_stamp()
    return data, path


def _load_html_source(args: argparse.Namespace) -> tuple[str, Optional[str]]:
    canon = getattr(args, "canonical_url", None) or None
    if args.stdin:
        return sys.stdin.read(), canon
    if args.html_file:
        p = args.html_file.expanduser().resolve()
        return p.read_text(encoding="utf-8", errors="replace"), canon
    if args.url:
        return fetch_html(args.url, timeout=args.timeout), args.url
    raise SystemExit("error: eine Quelle angeben: --url, --html-file oder --stdin.")


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
        "--url",
        help="PDP-URL (HTTP GET im Agenten, eigene TLS-Session). Für roco.cc-Browser-Workflow lieber --html-file + --canonical-url.",
    )
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
        "--quiet",
        action="store_true",
        help="Keine JSON-Ausgabe auf stdout (nur mit --write sinnvoll).",
    )
    ap.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        metavar="S",
        help="HTTP-Timeout in Sekunden für --url (default: 30).",
    )
    args = ap.parse_args()
    if args.canonical_url and not (args.html_file or args.stdin):
        raise SystemExit(
            "error: --canonical-url nur zusammen mit --html-file oder --stdin."
        )

    try:
        html, fallback_url = _load_html_source(args)
    except urllib.error.HTTPError as e:
        print(f"error: HTTP {e.code} {e.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"error: URL {e.reason}", file=sys.stderr)
        return 1
    except TimeoutError as e:
        print(f"error: Zeitüberschreitung beim Abruf: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: Netzwerk/OS: {e}", file=sys.stderr)
        return 1

    parsed = parse_pdp(html, fallback_url=fallback_url)
    if args.article:
        parsed["articleNumber"] = args.article
    if args.image_url and str(args.image_url).strip():
        parsed["imageUrl"] = str(args.image_url).strip()

    articles_root = args.articles_root.expanduser().resolve()

    if args.write:
        merged, path = merge_article_record(
            parsed,
            notes=args.notes,
            articles_root=articles_root,
            article_override=args.article,
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
