from __future__ import annotations

import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

from locobox_cli.adapters.sources.amintiri_feroviare.shop_site import normalize_article
from locobox_cli.domain.text import swiss_ss

_OPERATOR_COUNTRY = {
    "CFR": "RO",
    "CFR Calatori": "RO",
    "CFR Marfa": "RO",
    "CFR Infra": "RO",
    "CFR Infrast": "RO",
    "ATC": "RO",
    "Astra Trans Carpatic": "RO",
    "VTR": "RO",
    "Constantin Group": "RO",
    "ConstantinGroup": "RO",
    "Constantin Grup": "RO",
    "Green Cargo": "RO",
    "DB Cargo": "RO",
    "DB Cargo Rumania": "RO",
    "DB Cargo Rumänia": "RO",
    "DB Cargo Bulgaria": "BG",
    "BDZ": "BG",
    "BDZ Cargo": "BG",
    "Bulmarket": "BG",
    "ARF": "RO",
    "MAV": "HU",
    "MÁV": "HU",
    "GFR": "RO",
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


def _page_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([\s\S]*?)</title>", html, re.I)
    if not m:
        return ""
    t = _plain(m.group(1))
    t = re.sub(r"\s+kaufen\s*\|.*$", "", t, flags=re.I).strip()
    t = re.sub(r"^AF Models\s+", "", t, flags=re.I).strip()
    return t


def _product_heading(html: str) -> str:
    m = re.search(
        r'class=["\'][^"\']*\bproduct-name\b[^"\']*["\'][^>]*>([\s\S]*?)</(?:h1|h2|div|span)>',
        html,
        re.I,
    )
    if m:
        return _plain(m.group(1))
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
    if m:
        t = _plain(m.group(1))
        if t.lower() not in {"af models", "amintiri feroviare"}:
            return t
    return ""


def _english_block(html: str) -> str:
    m = re.search(
        r"English Version\s*</[^>]+>\s*([\s\S]{20,1200}?)\s*(?:PRODUSE SIMILARE|<h2|</div>)",
        html,
        re.I,
    )
    if m:
        return _plain(m.group(1))
    return ""


def _description(html: str, title: str) -> str:
    eng = _english_block(html)
    if eng and len(eng) > 40:
        desc = eng
    else:
        meta = swiss_ss((_meta(html, "description") or "").strip())
        # Drop Menzels shop fluff.
        meta = re.sub(
            r"\s*für\s+\d+[.,]\d+\s*€.*$",
            "",
            meta,
            flags=re.I,
        ).strip()
        meta = re.sub(
            r"\s*Menzels Lokschuppen.*$",
            "",
            meta,
            flags=re.I,
        ).strip()
        desc = meta or title
    # Prefer a short product property blurb from Menzels when present.
    m = re.search(
        r'<div[^>]*class=["\'][^"\']*product-detail-description-text[^"\']*["\'][^>]*>([\s\S]*?)</div>',
        html,
        re.I,
    )
    if m:
        blob = _plain(m.group(1))
        if len(blob) > 40:
            desc = blob
    if "Amintiri Feroviare" not in desc and "AF Models" not in desc:
        desc = f"{desc} H0-Modell (1:87) von Amintiri Feroviare / AF Models."
    return swiss_ss(desc)


def _image(html: str, base: str, article: str) -> Optional[str]:
    art = normalize_article(article)
    # Official media/images with AF{art} in filename
    for m in re.finditer(
        r'(?:src|data-zoom-image)=["\']([^"\']*media/images/[^"\']+)["\']',
        html,
        re.I,
    ):
        src = m.group(1)
        if art.lower() in src.lower() or f"af{art}".lower() in src.lower():
            return urljoin(base, src)
    for m in re.finditer(r'(?:src|data-src)=["\']([^"\']+)["\']', html, re.I):
        src = m.group(1)
        if "media/images/" in src and art.lower() in src.lower():
            return urljoin(base, src)
    # Menzels product images
    for m in re.finditer(
        r'(?:src|data-src)=["\']([^"\']*(?:thumbnail|media|product)[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']',
        html,
        re.I,
    ):
        src = m.group(1)
        if "logo" in src.lower() or "icon" in src.lower():
            continue
        if art.lower() in src.lower() or "af" in src.lower():
            return urljoin(base, src)
    og = _meta(html, "og:image")
    if og and og.startswith("http"):
        return og
    return None


def _era_from_text(blob: str) -> str:
    m = re.search(
        r"(?:Epoca|Epoche|Epoch|Era|Ep\.)\s*([IVX]+(?:\s*[-–/]\s*[IVX]+)?|\d)",
        blob,
        re.I,
    )
    if not m:
        return "Unbekannt"
    raw = m.group(1).strip().upper().replace("–", "-").replace("/", "-")
    digit = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI"}
    if raw in digit:
        return digit[raw]
    return re.sub(r"\s+", "", raw) or "Unbekannt"


def _operator_country(blob: str) -> tuple[str, str]:
    # Longer keys first
    for name in sorted(_OPERATOR_COUNTRY.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", blob, re.I):
            return name.replace("ConstantinGroup", "Constantin Group"), _OPERATOR_COUNTRY[name]
    if re.search(r"\bCFR\b", blob, re.I):
        return "CFR", "RO"
    return "Unbekannt", "RO"


def _categories(title: str, desc: str) -> list[str]:
    blob = f"{title}\n{desc}".lower()
    if re.search(r"dampf|aburi|steam", blob):
        return ["lokomotive", "dampflokomotive"]
    if re.search(r"diesel|diesellok", blob):
        return ["lokomotive", "diesellokomotive"]
    if re.search(
        r"electrica|e-lok|elektrolok|traxx|transmontana|060-ea|ea-3000|locomotiva electr",
        blob,
    ):
        return ["lokomotive", "elektrolokomotive"]
    if re.search(r"locomotiv|e-lok|lok\b", blob):
        return ["lokomotive", "elektrolokomotive"]
    if re.search(
        r"cisterna|kessel|refriger|kühl|container|sgn|eaos|güter|gueter|"
        r"flachwagen|salmmp|marfa|zagkks|zachks|zackks|bremen|linz|villach|klagenfurt",
        blob,
    ):
        return ["gueterwagen"]
    if re.search(
        r"vagon|wagen|ava200|cuseta|dormit|schlafwagen|liegewagen|personen|"
        r"salon|restaurant|speise|couchette|reisezug|dinamometric|set de doua|set 2",
        blob,
    ):
        return ["personenwagen"]
    return ["lokomotive", "elektrolokomotive"]


def _electric(cats: list[str], article: str, blob: str) -> str:
    if cats and cats[0] in {"personenwagen", "gueterwagen"}:
        return "Unbekannt"
    art = normalize_article(article)
    # Sound / digital retailer variants often start with 19
    if art.startswith("19") or re.search(r"\bDCC\b|\bSound\b", blob, re.I):
        return "DC-Digital"
    return "DC-Analog"


def _split_type_number(title: str, article: str) -> tuple[str, Optional[str], Optional[str]]:
    t = swiss_ss(title or "").strip()
    t = re.sub(rf"^(?:AF)?{re.escape(normalize_article(article))}\s+", "", t, flags=re.I).strip()
    t = re.sub(r"^AF Models\s+", "", t, flags=re.I).strip()
    livery = None
    qm = re.search(r"[\"“”«»''](.+?)[\"“”«»'']", t)
    if qm:
        livery = qm.group(1).strip() or None
        t = (t[: qm.start()] + t[qm.end() :]).strip()
    # Drop trailing epoch / scale noise
    t = re.sub(r"\s+Ep\.?\s*\d\s*$", "", t, flags=re.I).strip()
    t = re.sub(r"\s+Epoche\s*[IVX0-9-]+\s*$", "", t, flags=re.I).strip()

    m = re.search(
        r"(060-EA\d?|EA-?3000|TransMontana|TRAXX(?:3)?|060-DA|Reihe\s*46|"
        r"150\.\d+|AVA200|T2s|YA/?B|Bcm|Zagkks|Zachks|Zackks|Sgns|Rsfwc|Icehws|"
        r"Salmmp|MU)\b",
        t,
        re.I,
    )
    typ = m.group(1) if m else (t.split(",")[0].strip() if t else "Unbekannt")
    typ = re.sub(r"\s+", " ", typ).strip()

    num = None
    nm = re.search(
        r"\b(\d{2,3}-\d{3,4}-\d|\d{2,3}\s+\d{3,4}(?:-\d)?|91\s*53\s*0\s*\d{6}-\d|"
        r"480[-\s]?\d{3}|481[-\s]?\d{3}|86\s*\d{3}-\d|46\s*\d{3}|150\.\d+)\b",
        t,
    )
    if nm:
        num = re.sub(r"\s+", " ", nm.group(1)).strip()
    return typ or "Unbekannt", num, livery


def _uvp_from_html(html: str) -> Optional[float]:
    m = re.search(
        r'(?:itemprop=["\']price["\'][^>]*content=["\'](\d+(?:[.,]\d+)?)["\']|'
        r'content=["\'](\d+(?:[.,]\d+)?)["\'][^>]*itemprop=["\']price["\'])',
        html,
        re.I,
    )
    if m:
        raw = (m.group(1) or m.group(2) or "").replace(",", ".")
        try:
            val = float(raw)
            return val if val > 0 else None
        except ValueError:
            return None
    m = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€", html)
    if m:
        try:
            return float(m.group(1).replace(".", "").replace(",", "."))
        except ValueError:
            return None
    return None


def _menzels_sku(html: str) -> Optional[str]:
    m = re.search(
        r"Hersteller-Artikelnummer:</th>\s*<td[^>]*>\s*(AF)?([A-Za-z0-9-]+)",
        html,
        re.I,
    )
    if m:
        return normalize_article((m.group(1) or "") + m.group(2))
    return None


def parse_amintiri_feroviare_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    """Map AF Models PDP (official shop or Menzels) into Locobox article dict."""
    wanted = normalize_article(article)
    found = _menzels_sku(html)
    if found and found != wanted:
        raise ValueError(f"shop article {found} != requested {wanted}")

    title = _product_heading(html) or _page_title(html) or wanted
    # Prefer title that starts with article number
    pt = _page_title(html)
    if pt and (pt.startswith(wanted) or pt.upper().startswith(f"AF{wanted}")):
        title = pt

    desc = _description(html, title)
    blob = f"{title}\n{desc}"
    cats = _categories(title, desc)
    operator, country = _operator_country(blob)
    era = _era_from_text(blob)
    electric = _electric(cats, wanted, blob)
    model_type, model_number, livery = _split_type_number(title, wanted)

    # Named liveries from title leftovers
    for name in ("Puma", "Hora", "Matei Corvin", "King Carol", "Queen Maria", "Regina Maria", "Regele Carol"):
        if re.search(rf"\b{re.escape(name)}\b", title, re.I) and not livery:
            livery = name

    price = uvp_amount if uvp_amount is not None else _uvp_from_html(html)
    if price is not None and float(price) <= 0:
        price = None

    stamped = None
    sm = re.search(r"<!--\s*locobox-pdp-url:\s*(\S+)\s*-->", html)
    if sm:
        stamped = sm.group(1).strip()

    canon = (stamped or canonical_url or "").split("#")[0].strip()
    if not canon or "cauta?" in canon or "/search?" in canon:
        if "amintiriferoviare.com" in html.lower():
            m = re.search(
                rf'https?://www\.amintiriferoviare\.com/produs/[^"\']*{re.escape(wanted)}[^"\']*',
                html,
                re.I,
            )
            if m:
                canon = m.group(0)
        if (not canon or "cauta?" in canon) and "menzels" in html.lower():
            m = re.search(
                rf'https?://www\.menzels-lokschuppen\.de/[^"\']*af{re.escape(wanted)}[^"\']*',
                html,
                re.I,
            )
            if m:
                canon = m.group(0).split("?")[0]
    if not canon:
        from locobox_cli.adapters.sources.amintiri_feroviare.shop_site import (
            AmintiriFeroviareShopSite,
        )

        canon = AmintiriFeroviareShopSite().search_url(wanted)

    # Prefer official host in source.url when both appear; else keep canon.
    if "menzels-lokschuppen.de" in canon and "amintiriferoviare.com" in html:
        m = re.search(
            rf'https?://www\.amintiriferoviare\.com/produs/[^"\']*{re.escape(wanted)}[^"\']*',
            html,
            re.I,
        )
        if m:
            canon = m.group(0)

    img = _image(html, canon, wanted)

    tags: list[str] = []
    release = None
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
        ym = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if ym:
            release = ym.group(1)

    # Menzels-only URLs are fine on articles; tag allowlist is separate.
    notes = (
        "Daten von menzels-lokschuppen.de, automatisch aktualisiert."
        if "menzels-lokschuppen.de" in canon
        else "Daten von der Hersteller-Webseite, automatisch aktualisiert."
    )
    source: dict[str, Any] = {"url": canon, "notes": notes}
    if img and img.startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"amintiri-feroviare-{wanted}",
        "manufacturer": "Amintiri Feroviare",
        "articleNumber": wanted,
        "releaseDate": release,
        "uvp": {"amount": float(price), "currency": "EUR"} if price is not None else None,
        "model": {
            "country": country,
            "operator": operator,
            "type": model_type or "Unbekannt",
            "number": model_number,
            "livery": livery,
            "scale": "H0",
            "electricSystem": electric,
            "era": era,
        },
        "description": desc,
        "categories": cats,
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
