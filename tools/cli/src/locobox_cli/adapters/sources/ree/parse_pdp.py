from __future__ import annotations

import html as html_lib
import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.text import swiss_ss

_OPERATOR_COUNTRY = {
    "SNCF": "FR",
    "DB": "DE",
    "DB AG": "DE",
    "SBB": "CH",
    "ÖBB": "AT",
    "OBB": "AT",
    "NS": "NL",
    "FS": "IT",
    "CFL": "LU",
    "SNCB": "BE",
}


def _plain(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html_lib.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _product_jsonld(html: str) -> Optional[dict[str, Any]]:
    for mo in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    ):
        raw = mo.group(1).strip()
        if "Product" not in raw and '"sku"' not in raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    return item
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            return data
    return None


def _props(product: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for item in product.get("additionalProperty") or []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("name") or "").strip()
        val = str(item.get("value") or "").strip()
        if key and val:
            out.setdefault(key, []).append(val)
    return out


def _era_from_props(props: dict[str, list[str]]) -> str:
    eras = props.get("Époque") or props.get("Epoque") or []
    romans: list[str] = []
    for e in eras:
        m = re.match(r"^\s*(I{1,3}|IV|VI{0,3}|V)\b", e.strip())
        if m and m.group(1) not in romans:
            romans.append(m.group(1))
    if not romans:
        return "Unbekannt"
    if len(romans) == 1:
        return romans[0]
    return f"{romans[0]}-{romans[-1]}"


def _scale_from_props(props: dict[str, list[str]], title: str) -> str:
    vals = props.get("Échelle") or props.get("Echelle") or []
    blob = " ".join(vals) + " " + title
    if re.search(r"\bHOm\b", blob, re.I):
        return "HOm"
    if re.search(r"\bHOe\b", blob, re.I):
        return "HOe"
    if re.search(r"\bN\b", blob):
        return "N"
    if re.search(r"\bHO\b|\bH0\b", blob, re.I):
        return "H0"
    return "H0"


def _electric_from_props(props: dict[str, list[str]], title: str) -> str:
    tech = " ".join(props.get("Technologie") or []).lower()
    system = " ".join(props.get("Système d'exploitation") or props.get("Systeme d'exploitation") or []).lower()
    blob = f"{tech} {system} {title}".lower()
    ac = "3 rail" in blob or "3 rails" in blob or "courant alternatif" in blob
    digital = "digital" in blob or "dcc" in blob or "sound" in blob
    if ac and digital:
        return "AC-Digital"
    if ac:
        return "AC-Analog"
    if digital:
        return "DC-Digital"
    if "continu" in blob or "2 rail" in blob:
        return "DC-Analog"
    return "Unbekannt"


def _operator_country(props: dict[str, list[str]]) -> tuple[str, str]:
    vals = props.get("Compagnie") or []
    if not vals:
        return "Unbekannt", "FR"
    raw = vals[0].strip()
    key = raw.upper().replace("Ö", "O")
    for name, country in _OPERATOR_COUNTRY.items():
        if name.upper().replace("Ö", "O") == key or name.upper() == raw.upper():
            return name if name != "OBB" else "ÖBB", country
    return raw, "FR"


def _type_from_title(title: str, article: str) -> str:
    t = swiss_ss(_plain(title))
    t = re.sub(r"^\[HO[em]?\]\s*:\s*", "", t, flags=re.I)
    compact = ArticleNumber.parse(article).compact()
    t = re.sub(rf"\s*[-–—]\s*{re.escape(compact)}\s*$", "", t, flags=re.I)
    t = re.sub(rf"\s*[-–—]\s*{re.escape(article)}\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" -–—")
    return t or "Unbekannt"


def _price_from_product(product: dict[str, Any]) -> Optional[float]:
    offers = product.get("offers")
    if isinstance(offers, dict):
        raw = offers.get("price")
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None
    return None


def parse_ree_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
) -> dict[str, Any]:
    """
    Minimal PrestaShop PDP parse via Product JSON-LD (+ title heuristics).

    Shop SKUs are compact (MB263S); Locobox articleNumber stays hyphenated (MB-263S).
    """
    wanted = ArticleNumber.parse(article)
    product = _product_jsonld(html) or {}
    sku_raw = str(product.get("sku") or product.get("mpn") or "").strip()
    if sku_raw:
        shop = ArticleNumber.parse(sku_raw)
        if shop.compact() != wanted.compact():
            raise ValueError(f"shop article {shop.value} != requested {wanted.value}")
    title = str(product.get("name") or "")
    if not title:
        m = re.search(r"<title[^>]*>([\s\S]*?)</title>", html, re.I)
        title = _plain(m.group(1)) if m else ""
    props = _props(product)
    operator, country = _operator_country(props)
    images = product.get("image") or []
    img = images[0] if isinstance(images, list) and images else None
    if isinstance(img, dict):
        img = img.get("url")
    price = _price_from_product(product)

    tags: list[str] = []
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
    release = None
    if campaign_tag:
        ym = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if ym:
            release = ym.group(1)

    source: dict[str, Any] = {
        "url": canonical_url,
        "notes": "Daten von der Webseite, automatisch geupdated.",
    }
    if img and str(img).startswith("https://"):
        source["imageUrl"] = str(img)

    uvp = {"amount": price, "currency": "EUR"} if price is not None else None

    return {
        "schemaVersion": "1.0.0",
        "id": f"ree-{wanted.value.lower()}",
        "manufacturer": "REE Modèles",
        "articleNumber": wanted.value,
        "releaseDate": release,
        "uvp": uvp,
        "model": {
            "country": country,
            "operator": operator,
            "type": _type_from_title(title, wanted.value),
            "number": None,
            "livery": None,
            "scale": _scale_from_props(props, title),
            "electricSystem": _electric_from_props(props, title),
            "era": _era_from_props(props),
        },
        "description": swiss_ss(_plain(title)) if title else "Unbekannt",
        "categories": [],
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
