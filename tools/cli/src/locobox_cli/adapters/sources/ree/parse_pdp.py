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
        return "H0m"
    if re.search(r"\bHOe\b", blob, re.I):
        return "H0e"
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


def _categories_from_url(url: str, title: str, article: str) -> list[str]:
    u = (url or "").lower()
    blob = f"{u} {title} {article}".lower()
    if "/autorails/" in u or re.search(r"\brgp\b|autorail|triebwagen", blob):
        if re.search(r"électrique|electrique|tgv|electro", blob):
            return ["triebwagen", "elektrotriebwagen"]
        return ["triebwagen", "dieseltriebwagen"]
    if "/machines/" in u and re.search(r"\btgv\b", blob):
        return ["triebzug", "elektrotriebwagen"]
    # URL path first (shop taxonomy is reliable); do not infer electric from "BB".
    if "locomotives-diesel" in u or "/diesel" in u:
        return ["lokomotive", "diesellokomotive"]
    if "locomotives-electriques" in u or "/electrique" in u:
        return ["lokomotive", "elektrolokomotive"]
    if "locomotive-vapeur" in u or "/vapeur" in u or "locomotives-a-vapeur" in u:
        return ["lokomotive", "dampflokomotive"]
    if re.search(r"\bdiesel\b", blob):
        return ["lokomotive", "diesellokomotive"]
    if re.search(r"électrique|electrique", blob):
        return ["lokomotive", "elektrolokomotive"]
    if re.search(r"vapeur|dampf|MACHINE\s+\d|231\s*[KG]|141\s*[A-Z]", blob):
        return ["lokomotive", "dampflokomotive"]
    if article.upper().startswith("TGV") or re.search(r"\btgv\b", blob):
        return ["triebzug", "elektrotriebwagen"]
    if article.upper().startswith("VM"):
        return ["triebwagen", "dieseltriebwagen"]
    if article.upper().startswith("JM"):
        # Access electrics (CC 7100 etc.)
        return ["lokomotive", "elektrolokomotive"]
    return ["lokomotive"]


def _type_and_number_from_title(title: str, article: str) -> tuple[str, Optional[str], Optional[str]]:
    """Return (type, number, livery) with shop noise stripped."""
    t = swiss_ss(_plain(title))
    t = re.sub(r"^\[HO[em]?\]\s*:\s*", "", t, flags=re.I)
    compact = ArticleNumber.parse(article).compact()
    t = re.sub(rf"\s*[-–—]\s*{re.escape(compact)}\s*$", "", t, flags=re.I)
    t = re.sub(rf"\s*[-–—]\s*{re.escape(article)}\s*$", "", t, flags=re.I)
    t = re.sub(
        r"\s*[-–—,]\s*(?:DIGITAL\s+SOUND|DCC\s+SOUND|AC\s+SOUND|ANALOGIQUE|ANALOG)\s*$",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"\s*,?\s*Ep\.?\s*[IVX]+(?:\s*[-/]\s*[IVX]+)?\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" -–—,")

    number: Optional[str] = None
    livery: Optional[str] = None
    # Quoted marketing / train name
    m_liv = re.search(r"[“\"«]([^”\"»]+)[”\"»]", t)
    if m_liv:
        livery = swiss_ss(m_liv.group(1).strip())

    def _sncf_series(prefix: str, digits: str) -> tuple[str, Optional[str]]:
        """Serie in type, Laufziffern in number (reference-sncf-type-number.md)."""
        pref = prefix.upper()
        d = digits.strip()
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
        return f"{pref} {d}", d

    # Prefer short class token for type when BB/CC present
    m_type = re.search(r"\b(BB|CC)\s*(\d{2,5})\b", t, re.I)
    if m_type:
        typ, number = _sncf_series(m_type.group(1), m_type.group(2))
        return typ, number, livery
    # Autorail X-nnnn as running number with RGP / generic type below
    m_x = re.search(r"\bX[-\s]?(\d{3,4})\b", t, re.I)
    if m_x:
        number = f"X-{m_x.group(1)}"
    if re.search(r"\brgp\s*1\b", t, re.I):
        return "RGP 1", number, livery
    if re.search(r"\brgp\s*2\b", t, re.I):
        return "RGP 2", number, livery
    if re.search(r"\btgv\b", t, re.I):
        return "TGV PSE", number, livery
    # SNCF steam Pacific / Mikado in REE titles
    m_st = re.search(
        r"(?:MACHINE|Locomotive\s+à\s+vapeur)\s+(?:(\d)\s*[-–—]\s*)?(\d{3})\s*([A-Z])\s*(\d{1,4})\b",
        t,
        re.I,
    )
    if m_st:
        region, wheel, letter, eng = m_st.group(1), m_st.group(2), m_st.group(3).upper(), m_st.group(4)
        typ = f"{wheel} {letter}"
        number = f"{region}-{eng}" if region else eng
        return typ, number, livery
    m_141 = re.search(r"\b(141)\s*([A-Z])\s*(\d{2,4})\b", t, re.I)
    if m_141 and re.search(r"vapeur|MACHINE", t, re.I):
        return f"{m_141.group(1)} {m_141.group(2).upper()}", m_141.group(3), livery
    # HOm/HOe autorails (Billard / De Dion)
    t2 = re.sub(r"^\[[^\]]+\]\s*:\s*", "", t)
    t2 = re.sub(
        r"\s*[-–—,]\s*(?:DIGITAL\s+SOUND|DCC\s+SOUND|AC\s+SOUND|ANALOGIQUE|ANALOG)\s*$",
        "",
        t2,
        flags=re.I,
    )
    t2 = re.sub(r"\s*,?\s*Ep\.?\s*[IVX]+(?:\s*[-/]\s*[IVX]+)?\s*$", "", t2, flags=re.I)
    t2 = re.sub(r"\s+", " ", t2).strip(" -–—,")
    if re.search(r"billard|a80\s*d1|de\s*dion", t2, re.I):
        if re.search(r"a80\s*d1", t2, re.I):
            typ = "Billard A80 D1"
        elif re.search(r"de\s*dion", t2, re.I):
            typ = "De Dion ND"
        else:
            typ = "Autorail"
        m_n = re.search(r"\b(?:n[°ºo]|N°|X)\s*([0-9]{2,4})\b", t2, re.I)
        if m_n:
            number = m_n.group(1)
        return typ, number, livery
    return (t2 or t or "Unbekannt"), number, livery


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
    # Drop obviously broken HT/placeholder prices (full sound locos are >> 50 EUR).
    if price is not None and price < 50:
        price = None

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
    model_type, model_number, model_livery = _type_and_number_from_title(title, wanted.value)
    categories = _categories_from_url(canonical_url, title, wanted.value)

    return {
        "schemaVersion": "1.0.0",
        "id": f"ree-{wanted.value}",
        "manufacturer": "REE",
        "articleNumber": wanted.value,
        "releaseDate": release,
        "uvp": uvp,
        "model": {
            "country": country,
            "operator": operator,
            "type": model_type,
            "number": model_number,
            "livery": model_livery,
            "scale": _scale_from_props(props, title),
            "electricSystem": _electric_from_props(props, title),
            "era": _era_from_props(props),
        },
        "description": swiss_ss(_plain(title)) if title else "Unbekannt",
        "categories": categories,
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
