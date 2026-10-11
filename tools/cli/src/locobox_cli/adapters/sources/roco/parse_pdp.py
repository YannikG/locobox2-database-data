from __future__ import annotations

import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

from locobox_cli.domain.text import swiss_ss

_ART_FROM_URL = re.compile(r"/(\d{5,8})-[^/]+\.html", re.I)
_DR_ERA_DE = re.compile(r"^(I|II|III)(-(I|II|III))*$", re.I)

_CANON_ELECTRIC = frozenset({"DC-Analog", "DC-Digital", "AC-Analog", "AC-Digital"})

# Longest first so «Elektrotriebzug» wins over «Triebzug», «Elektrolokomotive» over «Elektrolok».
_TITLE_PREFIXES: tuple[str, ...] = tuple(
    sorted(
        {
            "Schienennahverkehrstriebzug",
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
            "Akkutriebwagen",
            "Steuerwagen",
            "Triebwagen",
            "Triebzug",
            "Dampflok",
            "Elektrolok",
            "Diesellok",
        },
        key=len,
        reverse=True,
    )
)

_OPERATOR_COUNTRY = {
    "DB AG": "DE",
    "DB": "DE",
    "DRG": "DE",
    "DR": "DE",
    "K.P.E.V.": "DE",
    "KPEV": "DE",
    "SBB": "CH",
    "ÖBB": "AT",
    "OBB": "AT",
    "NS": "NL",
    "SNCF": "FR",
    "FS": "IT",
    "PKP": "PL",
    "ČSD": "CZ",
    "CSD": "CZ",
    "ČD": "CZ",
    "CD": "CZ",
    "DSB": "DK",
}

# Shop/attribute variants → Locobox spelling (before country map).
_OPERATOR_ALIASES = {
    "DB-AG": "DB AG",
    "DBAG": "DB AG",
}

# Longest keys first so SNCF/DRG/DB AG win over NS/DR/DB.
_OPERATOR_KEYS: tuple[tuple[str, str], ...] = tuple(
    sorted(_OPERATOR_COUNTRY.items(), key=lambda kv: len(kv[0]), reverse=True)
)


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


def extract_specs(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    table_block = re.compile(
        r'<table[\s\S]*?\bid\s*=\s*["\']product-attribute-specs-table["\'][\s\S]*?>'
        r"([\s\S]*?)</table>",
        re.I,
    )
    for m in table_block.finditer(html):
        block = m.group(1)
        for cell in re.finditer(r"<td([^>]*)>(.*?)</td>", block, re.I | re.S):
            attrs, inner = cell.group(1), cell.group(2)
            if "data-th" not in attrs:
                continue
            dm = re.search(r'\bdata-th\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
            if not dm:
                continue
            label = html_lib.unescape(dm.group(1)).strip()
            text = _plain(inner)
            if label and text:
                out[label] = text
    return out


def _mm(raw: str) -> Optional[int]:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*mm\b", raw, re.I) or re.search(
        r"(\d+(?:[.,]\d+)?)", raw
    )
    if not m:
        return None
    return int(round(float(m.group(1).replace(",", "."))))


def _normalize_scale(raw: str) -> str:
    t = re.sub(r"\s+", "", swiss_ss(raw.strip())).lower()
    if t.startswith("h0e"):
        return "H0e"
    if t.startswith("h0") or t in {"ho", "hO".lower()}:
        return "H0"
    if t.startswith("tt"):
        return "TT"
    if t.startswith("n"):
        return "N"
    return "H0"


def _normalize_electric(raw: str) -> str:
    """Map Roco Stromsystem strings; bare Gleichstrom/DC without hint → DC-Analog."""
    if not raw or not str(raw).strip():
        return "DC-Analog"
    s0 = str(raw).strip()
    if s0 in _CANON_ELECTRIC:
        return s0
    if s0 == "dc":
        return "DC-Analog"
    if s0 == "ac":
        return "AC-Digital"

    t = swiss_ss(s0).upper()
    t = re.sub(r"\s+", " ", t)
    t = (
        t.replace("DC-ANALOG", "DC ANALOG")
        .replace("DC-DIGITAL", "DC DIGITAL")
        .replace("AC-ANALOG", "AC ANALOG")
        .replace("AC-DIGITAL", "AC DIGITAL")
    )

    is_ac = bool(re.search(r"\bAC\b|WECHSELSTROM", t))
    is_dc = bool(re.search(r"\bDC\b|GLEICHSTROM", t))
    has_analog = bool(re.search(r"\bANALOG", t))
    has_digital = bool(
        re.search(r"\b(DCC|MFX|MFX\+|MFXPLUS)\b", t, re.I)
    ) or ("DIGITAL" in t and not has_analog)

    if is_ac and is_dc:
        return "DC-Analog"

    if is_ac:
        if has_digital:
            return "AC-Digital"
        if has_analog:
            return "AC-Analog"
        return "AC-Digital"

    if is_dc:
        if has_digital:
            return "DC-Digital"
        if has_analog:
            return "DC-Analog"
        return "DC-Analog"

    if has_digital:
        return "DC-Digital"
    return "DC-Analog"


def _dr_country(era: str) -> str:
    """DR: Epoche I–III → DE (Reichsbahn), sonst DD (DDR)."""
    eu = (era or "").strip().upper().replace(" ", "")
    if not eu or eu == "UNBEKANNT":
        return "DD"
    if "IV" in eu:
        return "DD"
    if _DR_ERA_DE.fullmatch(eu):
        return "DE"
    return "DD"


def _operator_country(op: str, *, era: str = "") -> tuple[str, str]:
    key = op.strip()
    for bad, good in _OPERATOR_ALIASES.items():
        if key.upper() == bad.upper():
            key = good
            break
    ku = key.upper()
    for name, cc in _OPERATOR_KEYS:
        nu = name.upper()
        if ku == nu or ku.startswith(nu + " "):
            canon = "ÖBB" if name == "OBB" else name
            if canon == "DR":
                return canon, _dr_country(era)
            return canon, cc
    return key, "DE"


def _category_slug(prefix: str) -> str:
    s = swiss_ss(prefix.strip().lower())
    for a, b in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("é", "e")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "lokomotive"


def _parse_title(title: str) -> tuple[str, Optional[str], list[str]]:
    """Return type_line, operator, category slugs."""
    t = swiss_ss((title or "").strip())
    while True:
        nxt = re.sub(r"^\d{5,8}\s+", "", t, count=1)
        if nxt == t:
            break
        t = nxt.strip()
    cats: list[str] = ["lokomotive"]
    operator: Optional[str] = None
    type_line = t
    if "," in t:
        head, op = t.split(",", 1)
        operator = op.strip() or None
        type_line = head.strip()
    for pref in _TITLE_PREFIXES:
        if type_line.startswith(pref + " "):
            slug = _category_slug(pref)
            if slug and slug not in cats:
                cats.append(slug)
            type_line = type_line[len(pref) + 1 :].strip()
            break
    return type_line or "Unbekannt", operator, cats


def _image(html: str, base: str) -> Optional[str]:
    img = _meta(html, "og:image") or _meta(html, "og:image:secure_url")
    if not img:
        return None
    if img.startswith("//"):
        return "https:" + img
    if img.startswith("http"):
        return img
    return urljoin(base, img)


def parse_roco_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
) -> dict[str, Any]:
    canon = (_meta(html, "og:url") or canonical_url or "").split("#")[0].strip()
    title = _meta(html, "og:title") or ""
    desc = swiss_ss(_meta(html, "og:description") or title)
    price_raw = _meta(html, "product:price:amount")
    price = float(price_raw) if price_raw else 0.0

    art = article.strip()
    m = _ART_FROM_URL.search(canon)
    if m:
        found = m.group(1)
        if found != art:
            raise ValueError(f"shop article {found} != requested {art}")

    specs = extract_specs(html)
    type_line, title_op, cats = _parse_title(title)
    era = (specs.get("Epoche") or "Unbekannt").strip() or "Unbekannt"
    op_raw = (
        specs.get("Bahngesellschaft") or specs.get("Bahnverwaltung") or title_op or "Unbekannt"
    ).strip()
    op, country = _operator_country(op_raw, era=era)
    scale = _normalize_scale(specs.get("Spur") or "H0")
    electric = _normalize_electric(specs.get("Stromsystem") or specs.get("Antrieb") or "")
    decoder = (
        specs.get("Schnittstelle") or specs.get("Digitale Schnittstelle") or "Unbekannt"
    ).strip()
    luep = _mm(specs["Länge über Puffer"]) if specs.get("Länge über Puffer") else None
    min_r = _mm(specs["Mindestradius"]) if specs.get("Mindestradius") else None

    tags: list[str] = []
    release = None
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
        ym = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if ym:
            release = ym.group(1)

    model: dict[str, Any] = {
        "country": country,
        "operator": op,
        "type": type_line,
        "number": None,
        "livery": None,
        "scale": scale,
        "electricSystem": electric,
        "decoderInterface": decoder or "Unbekannt",
        "era": era,
    }
    if luep is not None:
        model["luepMm"] = luep
    if min_r is not None:
        model["minRadiusMm"] = min_r

    source: dict[str, Any] = {
        "url": canon or f"https://www.roco.cc/rde/catalogsearch/result/?q={art}",
        "notes": "Daten von der Webseite, automatisch geupdated.",
    }
    img = _image(html, canon or "https://www.roco.cc/")
    if img and img.startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"roco-{art}",
        "manufacturer": "Roco",
        "articleNumber": art,
        "releaseDate": release,
        "uvp": {"amount": price, "currency": "EUR"} if price > 0 else None,
        "model": model,
        "description": desc,
        "categories": cats,
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
