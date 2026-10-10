from __future__ import annotations

import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

from locobox_cli.domain.text import swiss_ss

_OPERATOR_COUNTRY = {
    "DB": "DE",
    "DB AG": "DE",
    "DR": "DE",
    "DRG": "DE",
    "SBB": "CH",
    "SBB Cargo": "CH",
    "ÖBB": "AT",
    "OBB": "AT",
    "NS": "NL",
    "SNCF": "FR",
    "FS": "IT",
    "PKP": "PL",
    "CD": "CZ",
    "ČSD": "CZ",
    "CSD": "CZ",
    "DSB": "DK",
    "MAV": "HU",
}


def _meta(html: str, prop: str) -> Optional[str]:
    m = re.search(
        rf'<meta\s+(?:property|name)=["\']{re.escape(prop)}["\']\s+content=["\']([^"\']+)["\']',
        html,
        re.I | re.S,
    )
    if not m:
        m = re.search(
            rf'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']{re.escape(prop)}["\']',
            html,
            re.I | re.S,
        )
    return html_lib.unescape(m.group(1).strip()) if m else None


def _plain(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html_lib.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _abs_url(base: str, maybe: str) -> str:
    u = (maybe or "").strip()
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith(("http://", "https://")):
        return u
    return urljoin(base, u)


def parse_attributes(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for mo in re.finditer(
        r'<td\s+class=["\']attribute-desc["\'][^>]*>(.*?)</td>\s*'
        r'<td\s+class=["\']attribute-value["\'][^>]*>(.*?)</td>',
        html,
        re.I | re.S,
    ):
        key = _plain(mo.group(1)).rstrip(":").strip()
        val = _plain(mo.group(2))
        if key and val:
            out[key] = val
    return out


def _price(html: str) -> float:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    for pat in (r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€", r"(\d+,\d{2})\s*€"):
        m = re.search(pat, text)
        if m:
            raw = re.sub(r"\.(?=\d{3},)", "", m.group(1)).replace(",", ".")
            return float(raw)
    return 0.0


def _main_image(html: str, base: str) -> str:
    for m in re.finditer(r"<img\b[^>]+>", html, re.I):
        tag = m.group(0)
        if "product__img" not in tag:
            continue
        sm = re.search(r'\bsrc=["\']([^"\']+)["\']', tag, re.I)
        if sm:
            return _abs_url(base, sm.group(1))
    return _abs_url(base, _meta(html, "og:image") or "")


def _type_line(html: str, og_title: str) -> str:
    for m in re.finditer(r"<h1\b[^>]*>(.*?)</h1>", html, re.I | re.S):
        t = swiss_ss(_plain(m.group(1)))
        if len(t) >= 4 and t.lower() not in {"startseite", "fehler", "404"}:
            return t
    t = re.sub(r"\s*\|\s*PIKO Webshop\s*$", "", og_title or "", flags=re.I)
    t = re.sub(r"\s+Modelleisenbahn\s+kaufen\s*$", "", t, flags=re.I)
    return swiss_ss(t.strip())


def _product_description(html: str) -> Optional[str]:
    """Shop marketing prose from PDP body (not the attribute table dump)."""
    m = re.search(
        r'class=["\']product__description_text[^"\']*["\'][^>]*>(.*?)</div>',
        html,
        re.I | re.S,
    )
    if not m:
        return None
    fragment = m.group(1)
    text = re.sub(r"<br\s*/?>", "\n\n", fragment, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    paragraphs: list[str] = []
    for para in re.split(r"\n\s*\n+", text):
        para = para.strip()
        if not para:
            continue
        # Feature lists are often joined with " | "
        bits = [re.sub(r"\s+", " ", bit).strip() for bit in re.split(r"\s*\|\s*", para)]
        bits = [bit for bit in bits if bit]
        if not bits:
            continue
        paragraphs.append("\n".join(bits))
    if not paragraphs:
        return None
    return swiss_ss("\n\n".join(paragraphs))


def _scale_from_type(type_line: str) -> str:
    if re.match(r"^TT\b", type_line, re.I):
        return "TT"
    if re.match(r"^G\b", type_line, re.I):
        return "G"
    if re.match(r"^N\b", type_line, re.I):
        return "N"
    return "H0"


def _electric_from_attrs(attrs: dict[str, str], description: str) -> str:
    raw = (attrs.get("Stromsystem") or "").lower()
    digital = "sound" in (attrs.get("Sound ja/nein") or "").lower() or "decoder" in description.lower()
    if "wechsel" in raw:
        return "AC-Digital" if digital else "AC-Analog"
    if "gleich" in raw:
        return "DC-Digital" if digital or "digital" in raw else "DC-Analog"
    return "DC-Digital" if digital else "DC-Analog"


def _operator_country(op: str) -> tuple[str, str]:
    key = op.strip()
    for name, cc in _OPERATOR_COUNTRY.items():
        if key.upper() == name.upper() or key.upper().startswith(name.upper() + " "):
            return name if name != "OBB" else "ÖBB", cc
    return key, "DE"


def parse_piko_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
) -> dict[str, Any]:
    title = _meta(html, "og:title") or ""
    attrs = parse_attributes(html)
    type_line = _type_line(html, title)
    desc = _product_description(html)
    if not desc:
        fallback = _meta(html, "og:description") or type_line or title
        fallback = re.sub(r"\s*\|\s*PIKO Webshop\s*$", "", fallback or "", flags=re.I)
        fallback = re.sub(r"\s+Modelleisenbahn\s+kaufen\s*$", "", fallback, flags=re.I)
        desc = swiss_ss(fallback.strip())

    shop_article = (attrs.get("Artikelnummer") or "").strip() or article.strip()
    if shop_article != article.strip():
        raise ValueError(f"shop article {shop_article} != requested {article}")

    op_raw = (attrs.get("Bahnverwaltung") or "").strip()
    operator, country = _operator_country(op_raw) if op_raw else ("Unbekannt", "DE")
    era = (attrs.get("Epoche") or "Unbekannt").strip() or "Unbekannt"
    decoder = (attrs.get("Digitale Schnittstelle") or "Unbekannt").strip() or "Unbekannt"
    img = _main_image(html, canonical_url)
    price = _price(html)
    electric = _electric_from_attrs(attrs, desc)

    model: dict[str, Any] = {
        "country": country,
        "operator": operator,
        "type": type_line or "Unbekannt",
        "number": None,
        "livery": None,
        "scale": _scale_from_type(type_line),
        "electricSystem": electric,
        "decoderInterface": decoder,
        "era": era,
    }

    tags: list[str] = []
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
    release = None
    if campaign_tag:
        m = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if m:
            release = m.group(1)

    source: dict[str, Any] = {
        "url": canonical_url,
        "notes": "Daten von der Webseite, automatisch geupdated.",
    }
    if img and str(img).startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"piko-{shop_article}",
        "manufacturer": "PIKO",
        "articleNumber": shop_article,
        "releaseDate": release,
        "uvp": {"amount": price, "currency": "EUR"},
        "model": model,
        "description": desc,
        "categories": [],
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
