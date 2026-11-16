from __future__ import annotations

import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

from locobox_cli.domain.text import swiss_ss

_OPERATOR_COUNTRY = {
    "DB AG": "DE",
    "DB Cargo": "DE",
    "DB": "DE",
    "DRG": "DE",
    "DR": "DE",
    "SBB": "CH",
    "SBB Cargo": "CH",
    "BLS": "CH",
    "ÖBB": "AT",
    "OBB": "AT",
    "NS": "NL",
    "SNCF": "FR",
    "SNCB": "BE",
    "NMBS": "BE",
    "LINEAS": "BE",
    "FS": "IT",
    "PKP": "PL",
    "ČSD": "CZ",
    "CSD": "CZ",
    "ČD": "CZ",
    "CD": "CZ",
    "DSB": "DK",
    "MAV": "HU",
    "CFL": "LU",
}

_OPERATOR_ALIASES = {
    "DB-AG": "DB AG",
    "DBAG": "DB AG",
    "MÁV": "MAV",
    "OBB": "ÖBB",
    "SNCB/NMBS": "SNCB",
    "NMBS/SNCB": "SNCB",
}

_TYPE_MATERIEL_CATS = {
    "HLE": ("lokomotive", "elektrolokomotive"),
    "HLD": ("lokomotive", "diesellokomotive"),
    "HLV": ("lokomotive", "dampflokomotive"),
    "AUTOR": ("lokomotive", "triebwagen"),
    "AUT": ("lokomotive", "triebwagen"),
}

_PAYS_COUNTRY = {
    "D": "DE",
    "DE": "DE",
    "ALLEMAGNE": "DE",
    "DEUTSCHLAND": "DE",
    "CH": "CH",
    "SUISSE": "CH",
    "SCHWEIZ": "CH",
    "A": "AT",
    "AT": "AT",
    "AUTRICHE": "AT",
    "ÖSTERREICH": "AT",
    "OSTERREICH": "AT",
    "B": "BE",
    "BE": "BE",
    "BELGIQUE": "BE",
    "BELGIEN": "BE",
    "F": "FR",
    "FR": "FR",
    "FRANCE": "FR",
    "NL": "NL",
    "I": "IT",
    "IT": "IT",
    "CZ": "CZ",
    "PL": "PL",
    "DK": "DK",
    "HU": "HU",
    "LU": "LU",
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
    t = re.sub(r"<[^>]+>", " ", fragment)
    t = html_lib.unescape(t)
    return swiss_ss(re.sub(r"\s+", " ", t).strip())


def extract_features(html: str) -> dict[str, str]:
    """Parse PrestaShop ``product-features`` dl/dt/dd blocks (ALIMENTATION, ECHELLE, …)."""
    out: dict[str, str] = {}
    for m in re.finditer(
        r'<dt[^>]*class=["\'][^"\']*name[^"\']*["\'][^>]*>\s*([^<]+?)\s*</dt>\s*'
        r'<dd[^>]*class=["\'][^"\']*value[^"\']*["\'][^>]*>\s*([^<]+?)\s*</dd>',
        html,
        re.I | re.S,
    ):
        label = html_lib.unescape(m.group(1)).strip()
        value = html_lib.unescape(m.group(2)).strip()
        if label and value and label not in out:
            out[label] = value
    # Fallback: JSON embedded in data-product features array
    if not out:
        for m in re.finditer(
            r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"([^"]+)"',
            html,
        ):
            label = html_lib.unescape(m.group(1)).strip()
            value = html_lib.unescape(m.group(2)).strip()
            if label and value and label not in out:
                out[label] = value
    return out


def extract_reference(html: str) -> Optional[str]:
    m = re.search(
        r'itemprop=["\']sku["\'][^>]*>\s*([^<]+?)\s*<',
        html,
        re.I,
    )
    if m:
        return _plain(m.group(1))
    m = re.search(
        r'Artikel-Nr\.?\s*</label>\s*<span[^>]*>\s*([^<]+?)\s*</span>',
        html,
        re.I,
    )
    if m:
        return _plain(m.group(1))
    m = re.search(
        r'"reference"\s*:\s*"([^"]+)"',
        html,
    )
    if m:
        return html_lib.unescape(m.group(1)).strip()
    return None


def _h1(html: str) -> str:
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
    return swiss_ss(_plain(m.group(1))) if m else ""


def _normalize_scale(raw: str) -> str:
    t = re.sub(r"\s+", "", swiss_ss(raw.strip())).upper()
    if t in {"HO", "H0", "HÖ"}:
        return "H0"
    if t.startswith("H0E") or t.startswith("HOE"):
        return "H0e"
    if t.startswith("TT"):
        return "TT"
    if t.startswith("N"):
        return "N"
    return "H0"


def _normalize_electric(raw: str) -> str:
    if not raw or not str(raw).strip():
        return "DC-Analog"
    t = swiss_ss(str(raw).strip()).upper()
    t = re.sub(r"\s+", " ", t)
    is_ac = bool(re.search(r"\bAC\b|WECHSELSTROM", t))
    is_dc = bool(re.search(r"\bDC\b|GLEICHSTROM", t))
    has_digital = bool(re.search(r"\b(DCC|DIGITAL|SOUND|MFX)\b", t))
    if is_ac and not is_dc:
        return "AC-Digital" if has_digital or "AC" in t else "AC-Analog"
    if is_ac:
        return "AC-Digital"
    if has_digital:
        return "DC-Digital"
    return "DC-Analog"


def _normalize_era(raw: str) -> str:
    t = swiss_ss((raw or "").strip())
    if not t or t in {"---", "-", "?"}:
        return "Unbekannt"
    # Shop often uses Arabic or Roman; keep Roman letters uppercase.
    return t.upper() if re.fullmatch(r"[ivxlcdm]+", t, re.I) else t


def _operator_country(op: str) -> tuple[str, str]:
    key = op.strip()
    for bad, good in _OPERATOR_ALIASES.items():
        if key.upper() == bad.upper():
            key = good
            break
    for name, cc in sorted(_OPERATOR_COUNTRY.items(), key=lambda kv: len(kv[0]), reverse=True):
        if key.upper() == name.upper() or key.upper().startswith(name.upper() + " "):
            return ("ÖBB" if name == "OBB" else name), cc
    return key, "DE"


def _operator_from_title(title: str, pays: str) -> tuple[str, str]:
    t = swiss_ss(title or "")
    for name in sorted(_OPERATOR_COUNTRY, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", t, re.I):
            return _operator_country(name)
    pays_key = (pays or "").strip().upper()
    if pays_key and pays_key not in {"---", "-", "?"}:
        cc = _PAYS_COUNTRY.get(pays_key)
        if cc:
            return "Unbekannt", cc
    return "Unbekannt", "DE"


def _categories_from_materiel(raw: str) -> list[str]:
    key = (raw or "").strip().upper()
    cats = _TYPE_MATERIEL_CATS.get(key)
    if cats:
        return list(cats)
    return ["lokomotive"]


def _image(html: str, base: str) -> Optional[str]:
    img = _meta(html, "og:image")
    if not img:
        return None
    if img.startswith("//"):
        return "https:" + img
    if img.startswith("http"):
        return img
    return urljoin(base, img)


def _canon_reference(raw: str) -> str:
    """Strip spaces / DC|AC / Sound ``S`` so ``13001 DC`` matches queue ``13001``."""
    s = re.sub(r"\s+", "", raw.strip())
    s = re.sub(r"(?:DC|AC)?S?$", "", s, flags=re.I)
    return s


def parse_lsmodels_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    """
    Map lsmodels.eu PrestaShop PDP into a Locobox article dict.

    Shop is often catalog-only (``show_prices: false``); UVP may be null.
    Manufacturer string ``L.S.Models`` slugifies to ``lsmodels`` (folder/id).
    """
    art = article.strip().replace(" ", "")
    ref = extract_reference(html)
    if ref:
        found = _canon_reference(ref)
        if found != art:
            raise ValueError(f"shop article {found} != requested {art}")

    features = extract_features(html)
    title = _h1(html) or swiss_ss(_meta(html, "og:title") or art)
    desc = swiss_ss(_meta(html, "og:description") or title)
    # Prefer longer description tab if present.
    m_desc = re.search(
        r'<div[^>]*class=["\'][^"\']*product-description[^"\']*["\'][^>]*>([\s\S]*?)</div>',
        html,
        re.I,
    )
    if m_desc:
        long_desc = _plain(m_desc.group(1))
        if len(long_desc) > len(desc):
            desc = long_desc

    era = _normalize_era(features.get("EPOQUE") or "")
    scale = _normalize_scale(features.get("ECHELLE") or "HO")
    electric = _normalize_electric(features.get("ALIMENTATION") or "")
    operator, country = _operator_from_title(title, features.get("PAYS") or "")
    cats = _categories_from_materiel(features.get("TYPE DE MATERIEL") or "")

    canon = (_meta(html, "og:url") or canonical_url or "").split("#")[0].strip()
    img = _image(html, canon or "https://lsmodels.eu/")

    tags: list[str] = []
    release = None
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
        ym = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if ym:
            release = ym.group(1)

    amount: Optional[float] = None
    if uvp_amount is not None and float(uvp_amount) > 0:
        amount = float(uvp_amount)

    model: dict[str, Any] = {
        "country": country,
        "operator": operator,
        "type": title or "Unbekannt",
        "number": None,
        "livery": None,
        "scale": scale,
        "electricSystem": electric,
        "era": era,
    }

    source: dict[str, Any] = {
        "url": canon or f"https://lsmodels.eu/de/suche?controller=search&s={art}",
        "notes": "Daten von lsmodels.eu, automatisch geupdated.",
    }
    if img and img.startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"lsmodels-{art}",
        # L.S.Models slugifies to lsmodels (matches Manufacturer.slug / folder).
        "manufacturer": "L.S.Models",
        "articleNumber": art,
        "releaseDate": release,
        "uvp": {"amount": amount, "currency": "EUR"} if amount is not None else None,
        "model": model,
        "description": desc,
        "categories": cats,
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
