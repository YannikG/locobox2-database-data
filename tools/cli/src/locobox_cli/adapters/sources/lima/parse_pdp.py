from __future__ import annotations

import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

from locobox_cli.domain.text import swiss_ss

_ART_FROM_URL = re.compile(r"/products/[^/]*-(?P<sku>h[lc]\d{3,5})/?$", re.I)
_SKU_META = re.compile(
    r'(?:product:retailer_item_id["\']\s+content=["\']|'
    r'"sku"\s*:\s*"|'
    r"Codice articolo:\s*<br>\s*|"
    r"Item code:\s*)"
    r"(?P<sku>H[LC]\d{3,5})",
    re.I,
)

_OPERATOR_COUNTRY = {
    "FS": "IT",
    "FS TRENITALIA": "IT",
    "TRENITALIA": "IT",
    "TRENITALIA TPER": "IT",
    "FER": "IT",
    "SBB": "CH",
    "DB AG": "DE",
    "DB": "DE",
    "ÖBB": "AT",
    "OBB": "AT",
    "SNCF": "FR",
}

_OPERATOR_ALIASES = {
    "FS TRENITALIA": "FS",
    "FS-TRENITALIA": "FS",
    "TRENITALIA TPER": "Trenitalia Tper",
}

_FLAG_COUNTRY = {
    "italy": "IT",
    "italia": "IT",
    "switzerland": "CH",
    "schweiz": "CH",
    "germany": "DE",
    "deutschland": "DE",
    "austria": "AT",
    "österreich": "AT",
    "france": "FR",
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
    return swiss_ss(re.sub(r"\s+", " ", t).strip())


def _h1(html: str) -> str:
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
    return swiss_ss(_plain(m.group(1))) if m else ""


def extract_specs(html: str) -> dict[str, str]:
    """Parse limamodel.it ``<dt class="spec__title">`` / ``<dd class="spec__description">``."""
    out: dict[str, str] = {}
    for m in re.finditer(
        r'<dt[^>]*class=["\'][^"\']*spec__title[^"\']*["\'][^>]*>\s*([^<]+?)\s*</dt>\s*'
        r'<dd[^>]*class=["\'][^"\']*spec__description[^"\']*["\'][^>]*>\s*([^<]+?)\s*</dd>',
        html,
        re.I,
    ):
        key = html_lib.unescape(m.group(1)).strip()
        val = swiss_ss(html_lib.unescape(m.group(2)).strip())
        if key and val and key not in out:
            out[key] = val
    return out


def _normalize_scale(raw: str) -> str:
    t = swiss_ss((raw or "").strip()).lower()
    if "h0e" in t or "hoe" in t:
        return "H0e"
    if "h0" in t or "ho gauge" in t or "1:87" in t or "hö" in t:
        return "H0"
    if re.search(r"\btt\b", t):
        return "TT"
    if re.search(r"\bn\b", t) or "1:160" in t:
        return "N"
    return "H0"


def _normalize_era(raw: str) -> str:
    m = re.search(r"\b(I{1,3}|IV|V|VI|VII)\b", (raw or "").upper())
    return m.group(1) if m else "Unbekannt"


def _normalize_electric(dcc_raw: str, description: str) -> str:
    blob = f"{dcc_raw} {description}".lower()
    has_sound = "sound" in blob
    has_digital = any(
        x in blob for x in ("dcc ready", "dcc fitted", "decoder", "digital", "mfx")
    ) or bool(re.search(r"\b\d+\s*pin\s*socket", blob))
    if has_sound or "dcc fitted" in blob or "with decoder" in blob:
        return "DC-Digital"
    if has_digital:
        # Lima Expert H0 is 2-rail DC; socket without decoder → analog ready.
        return "DC-Analog"
    return "DC-Analog"


def _min_radius_mm(raw: str) -> Optional[float]:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*mm", raw or "", re.I)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def _operator_country(
    livrea: str, title: str, flag: str
) -> tuple[str, str]:
    blob = f"{livrea} {title}".strip()
    for bad, good in _OPERATOR_ALIASES.items():
        if re.search(rf"\b{re.escape(bad)}\b", blob, re.I):
            blob = re.sub(rf"\b{re.escape(bad)}\b", good, blob, count=1, flags=re.I)
            break
    for name, cc in sorted(_OPERATOR_COUNTRY.items(), key=lambda kv: len(kv[0]), reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", blob, re.I):
            canon = "ÖBB" if name == "OBB" else (
                "Trenitalia Tper" if name == "TRENITALIA TPER" else name
            )
            if canon in {"FS TRENITALIA", "TRENITALIA"}:
                canon = "FS"
            return canon, cc
    flag_cc = _FLAG_COUNTRY.get((flag or "").strip().lower())
    if flag_cc:
        return "Unbekannt", flag_cc
    return "Unbekannt", "IT"


def _type_from_title(title: str, article: str) -> str:
    t = swiss_ss((title or "").strip())
    # Drop leading SKU.
    t = re.sub(rf"^{re.escape(article)}\s*", "", t, flags=re.I).strip()
    return t or "Unbekannt"


def _image(html: str, base: str) -> Optional[str]:
    img = _meta(html, "og:image")
    if not img:
        return None
    if img.startswith("//"):
        return "https:" + img
    if img.startswith("http"):
        return img
    return urljoin(base, img)


def _find_shop_article(html: str, canonical_url: str, article: str) -> str:
    m = _SKU_META.search(html)
    if m:
        return m.group("sku").upper()
    um = _ART_FROM_URL.search(canonical_url.split("?", 1)[0])
    if um:
        return um.group("sku").upper()
    retailer = _meta(html, "product:retailer_item_id")
    if retailer and re.fullmatch(r"H[LC]\d{3,5}", retailer.strip(), re.I):
        return retailer.strip().upper()
    return article.strip().upper()


def parse_lima_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    canon = (_meta(html, "og:url") or canonical_url or "").split("#")[0].strip()
    shop_article = _find_shop_article(html, canon, article)
    want = article.strip().upper()
    if shop_article != want:
        raise ValueError(f"product article {shop_article} != requested {want}")

    title = _h1(html) or swiss_ss(_meta(html, "og:title") or article)
    desc = swiss_ss(_meta(html, "og:description") or title)
    specs = extract_specs(html)
    era = _normalize_era(specs.get("Epoca") or specs.get("Epoch") or "")
    scale = _normalize_scale(
        specs.get("Scala articolo") or specs.get("Item Scale") or "H0"
    )
    livrea = (specs.get("Livrea/Logo") or specs.get("Livery/Owner logo") or "").strip()
    flag = (specs.get("Bandiera") or specs.get("Region Flag") or "").strip()
    operator, country = _operator_country(livrea, title, flag)
    dcc = specs.get("DCC") or specs.get("DCC Status") or ""
    electric = _normalize_electric(dcc, desc)
    decoder = (dcc or "Unbekannt").strip() or "Unbekannt"
    min_r = _min_radius_mm(
        specs.get("Curva minima (mm)") or specs.get("Minimum Curve (mm)") or ""
    )

    price_raw = _meta(html, "product:price:amount")
    if uvp_amount is not None:
        amount = float(uvp_amount)
    elif price_raw:
        amount = float(price_raw)
    else:
        amount = 0.0

    tags: list[str] = []
    release = None
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
        ym = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if ym:
            release = ym.group(1)

    model: dict[str, Any] = {
        "country": country,
        "operator": operator,
        "type": _type_from_title(title, shop_article),
        "number": None,
        "livery": livrea or None,
        "scale": scale,
        "electricSystem": electric,
        "decoderInterface": decoder,
        "era": era,
    }
    if min_r is not None:
        model["minRadiusMm"] = min_r

    source: dict[str, Any] = {
        "url": canon
        or f"https://it.limamodel.it/search?query={shop_article}",
        "notes": "Daten von limamodel.it (Hornby International), automatisch geupdated.",
    }
    img = _image(html, canon or "https://it.limamodel.it/")
    if img and img.startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"lima-{shop_article}",
        "manufacturer": "Lima",
        "articleNumber": shop_article,
        "releaseDate": release,
        "uvp": {"amount": amount, "currency": "EUR"} if amount > 0 else None,
        "model": model,
        "description": desc,
        "categories": ["lokomotive"],
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
