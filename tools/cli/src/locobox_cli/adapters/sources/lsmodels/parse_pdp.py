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
    "AUTOR": ("triebwagen", "dieseltriebwagen"),
    "AUT": ("triebwagen", "dieseltriebwagen"),
    "AM": ("triebwagen", "elektrotriebwagen"),
    "VOIT": ("wagen",),
    "VOITURE": ("wagen",),
    "WAGON": ("wagen",),
}

# PAYS feature on lsmodels.eu is often the EVU name (SNCF, SNCB), not ISO.
_PAYS_OPERATOR = {
    "SNCF": ("SNCF", "FR"),
    "SNCB": ("SNCB", "BE"),
    "NMBS": ("SNCB", "BE"),
    "SNCB/NMBS": ("SNCB", "BE"),
    "NMBS/SNCB": ("SNCB", "BE"),
    "SBB": ("SBB", "CH"),
    "CFF": ("SBB", "CH"),
    "FFS": ("SBB", "CH"),
    "DB": ("DB", "DE"),
    "DB AG": ("DB AG", "DE"),
    "DB CARGO": ("DB Cargo", "DE"),
    "ÖBB": ("ÖBB", "AT"),
    "OBB": ("ÖBB", "AT"),
    "NS": ("NS", "NL"),
    "CFL": ("CFL", "LU"),
    "LINEAS": ("LINEAS", "BE"),
    "FS": ("FS", "IT"),
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
        r'<dd[^>]*>\s*([^<]+?)\s*</dd>',
        html,
        re.I | re.S,
    ):
        label = html_lib.unescape(m.group(1)).strip()
        value = html_lib.unescape(m.group(2)).strip()
        if label and value and label not in out:
            out[label] = value
    # Fallback: JSON features in data-product (often HTML-entity escaped).
    if len(out) < 2:
        blob = html_lib.unescape(html)
        for m in re.finditer(
            r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"([^"]*)"',
            blob,
        ):
            label = m.group(1).strip()
            value = m.group(2).strip()
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
    t = t.upper() if re.fullmatch(r"[ivxlcdm]+", t, re.I) else t
    return _strip_era_subletters(t)


def _strip_era_subletters(era: str) -> str:
    """Epoche ohne Unterstufen: ``IVC-VA`` → ``IV-V``, ``IIIB-C`` → ``III``, ``VB`` → ``V``."""
    if not re.fullmatch(r"[IVX]+[A-C]?(?:\s*-\s*[IVX]*[A-C]?)*", era):
        return era
    parts: list[str] = []
    for tok in re.split(r"\s*-\s*", era):
        base = re.sub(r"[A-C]$", "", tok)
        if base and (not parts or parts[-1] != base):
            parts.append(base)
    return "-".join(parts) or era


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
    # «DB Zulassung» = homologation, not operator DB
    t_op = re.sub(r"\bDB\s+Zulassung\b", " ", t, flags=re.I)
    for name in sorted(_OPERATOR_COUNTRY, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", t_op, re.I):
            return _operator_country(name)
    pays_key = (pays or "").strip().upper()
    if pays_key and pays_key not in {"---", "-", "?"}:
        if pays_key in _PAYS_OPERATOR:
            return _PAYS_OPERATOR[pays_key]
        # Alias lookup (case variants already uppercased)
        for alias, pair in _PAYS_OPERATOR.items():
            if pays_key == alias.upper():
                return pair
        cc = _PAYS_COUNTRY.get(pays_key)
        if cc:
            return "Unbekannt", cc
    return "Unbekannt", "DE"


def _categories_from_materiel(raw: str, *, categorie: str = "", title: str = "") -> list[str]:
    key = (raw or "").strip().upper()
    cats = _TYPE_MATERIEL_CATS.get(key)
    if cats:
        return list(cats)
    cat = (categorie or "").strip().upper()
    blob = f"{cat} {swiss_ss(title or '')}".upper()
    if re.search(
        r"\b(?:VOITURE|WAGON|APM|BPM|I10|I2|I5|I6|M6|OCEM|WL\b|NIGHTJET|"
        r"SPEISEWAGEN|GROSSRAUMWAGEN|VTU|GRIL\s+EXPRESS|EW\s*I|"
        r"BVCMZ|WLABMZ|CIWL)\b",
        blob,
    ):
        return ["wagen"]
    if re.search(r"\b(?:PANTO|FAHRSTROMABNEHMER|PANTOGRAPHE)\b", blob):
        return ["zubehoer"]
    if re.search(r"\b(?:X\s*\d{3,4}|AUTORAIL|EAD)\b", blob):
        return ["triebwagen", "dieseltriebwagen"]
    if re.search(r"\b(?:AGC|ET\s*\d+|TRIEBWAGEN|RER|Z\s+\d{4,5})\b", blob):
        return ["triebwagen", "elektrotriebwagen"]
    if re.search(r"\b(?:VECTRON|SMARTRON|HLE|BB|CC|BR\s*\d|E\s*\d{3})\b", blob):
        return ["lokomotive", "elektrolokomotive"]
    return ["lokomotive"]


def _sncf_series_and_running(prefix: str, digits: str) -> tuple[str, Optional[str]]:
    """BB/CC digit block → (series type, running number or None)."""
    pref = prefix.upper()
    d = digits.strip()
    if not d.isdigit():
        return f"{pref} {d}", d
    if pref == "BB" and len(d) == 5 and d.startswith(("222", "223")):
        # BB 22200 «Nez cassé» family (222xx / 223xx)
        return "BB 22200", None if d == "22200" else d
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


def split_lsmodels_title(
    title: str,
    *,
    categorie: str = "",
) -> tuple[str, Optional[str], Optional[str]]:
    """
    Split PrestaShop H1 into (type, number, livery).

    Conservative: when no clear class/number pattern matches, type stays the
    full title and number/livery stay None (autofix / review later).
    """
    raw = swiss_ss((title or "").strip())
    if not raw:
        return "Unbekannt", None, None

    # Strip trailing Ep. / Epoche markers from the working string.
    work = re.sub(r"\s*,?\s*Ep\.?\s*[IVX0-9][-IVX0-9]*\s*$", "", raw, flags=re.I).strip()
    cat = swiss_ss((categorie or "").strip())

    def _livery_from_rest(rest: str) -> Optional[str]:
        r = rest.strip(" ,;/-")
        if not r or len(r) < 2:
            return None
        # Drop ultra-long marketing dumps in type; keep a short livery hint.
        if len(r) > 80:
            r = r[:80].rstrip(" ,;")
        return r

    # 1) HLE class (+ optional running number elsewhere)
    m = re.match(
        r"^(HLE\s*\d+(?:\s*²)?)\s*(?:,|/|\s+)?\s*(.*)$",
        work,
        re.I,
    )
    if m:
        typ = re.sub(r"\s+", " ", m.group(1).upper().replace("HLE", "HLE ").strip())
        typ = re.sub(r"HLE\s+", "HLE ", typ)
        rest = m.group(2).strip()
        # «HLE 13 SNCB/NMBS» → no livery
        if re.fullmatch(r"(?:SNCB|NMBS)(?:\s*/\s*(?:SNCB|NMBS))?", rest, re.I):
            return typ, None, None
        return typ, None, _livery_from_rest(rest) if rest else None

    def _hle_from_running(num: str) -> str:
        # Prefer CATEGORIE «HLE 13» / «SÉRIE 13»
        m_cat = re.search(r"\b(?:HLE|S[ÉE]RIE)\s*(\d+)\b", cat, re.I)
        if m_cat:
            return f"HLE {m_cat.group(1)}"
        if num[:2] in {"11", "12", "13", "18", "21", "27"}:
            return f"HLE {num[:2]}"
        if re.match(r"^27", num) or num.startswith("27"):
            return "HLE 27"
        return "HLE"

    # 2) Leading running number then comma (HLE shop form: «1312, …» / «2702, CERTUS»)
    # Note: bare «120, …» is DB BR 120, not Belgian HLE 12 — require 4+ digits
    # or explicit HLE/SNCB markers / CATEGORIE.
    m = re.match(r"^(\d{3,5}|xx|\d{2}xx)\s*[,–—-]\s*(.+)$", work, re.I)
    if m:
        num_raw = m.group(1)
        rest = m.group(2).strip()
        explicit = bool(
            re.search(r"\bHLE\b|\bS[ÉE]RIE\s*\d+", cat, re.I)
            or re.search(
                r"\b(?:LINEAS|SNCB|NMBS|B-Logistics|CERTUS|Magelan)\b",
                work,
                re.I,
            )
        )
        looks_be = (
            num_raw[:2].isdigit()
            and num_raw[:2] in {"11", "12", "13", "18", "21", "27"}
            and (len(re.sub(r"\D", "", num_raw)) >= 4 or "xx" in num_raw.lower())
        )
        if explicit or looks_be:
            if "xx" in num_raw.lower():
                digits = re.sub(r"[^\d]", "", num_raw)[:2]
                return (f"HLE {digits}" if digits else "HLE"), None, _livery_from_rest(rest)
            return _hle_from_running(num_raw), num_raw, _livery_from_rest(rest)

    # Belgian HLE without comma: «1347 blanche / wit (SNCB / NMBS)»
    m = re.match(r"^(\d{3,5})\s+(.+)$", work)
    if m and re.search(r"\b(?:LINEAS|SNCB|NMBS)\b", work, re.I):
        num = m.group(1)
        rest = m.group(2).strip()
        return _hle_from_running(num), num, _livery_from_rest(rest)

    # 3) SNCF BB / CC (incl. UIC «BB 107258»)
    m = re.match(r"^(BB|CC)\s*(\d{3,6})\b\s*,?\s*(.*)$", work, re.I)
    if m:
        digits = m.group(2)
        if len(digits) == 6 and digits.startswith("10"):
            # UIC-ish BB 7200 family anschrift
            return f"{m.group(1).upper()} 7200", digits, _livery_from_rest(m.group(3))
        series, running = _sncf_series_and_running(m.group(1), digits)
        return series, running, _livery_from_rest(m.group(3))

    # 4) Autorail X#### / X ####
    m = re.match(r"^X\s*[-]?\s*(\d{3,4})\b\s*,?\s*(.*)$", work, re.I)
    if m:
        # Serie X 4500 (Nr. 4501–4800), Laufnummer wie bei REE «X-2900» mit X-Präfix
        num = int(m.group(1))
        typ = "X 4500" if 4501 <= num <= 4800 else f"X {num}"
        return typ, f"X {m.group(1)}", _livery_from_rest(m.group(2))

    # 5) AGC / Z #####
    m = re.match(r"^Z\s+(\d{4,5})\b\s*,?\s*(.*)$", work, re.I)
    if m:
        return "AGC", m.group(1), _livery_from_rest(m.group(2))

    # 5b) ET 403 Triebzug
    m = re.match(r"^(ET\s*\d{3})\b\s*,?\s*(.*)$", work, re.I)
    if m:
        typ = re.sub(r"(?i)^et\s*", "ET ", m.group(1)).strip()
        return typ, None, _livery_from_rest(m.group(2))

    # 5c) DB BR with check digit «184 103-2» / «181 001-9» / «E 410 011»
    m = re.match(
        r"^(E\s*)?(\d{2,3})\s+(\d{3}(?:-\d)?)\b\s*,?\s*(.*)$",
        work,
        re.I,
    )
    if m and not re.match(r"^(?:BB|CC|HLE)\b", work, re.I):
        br = m.group(2)
        num = m.group(3)
        rest = m.group(4)
        prefix = "E " if m.group(1) else "BR "
        return f"{prefix}{br}".replace("E  ", "E "), f"{br} {num}", _livery_from_rest(rest)

    # 5d) Short «120, verkehrsrot…» → BR 120
    m = re.match(r"^(1[12]0)\s*,\s*(.+)$", work)
    if m:
        return f"BR {m.group(1)}", None, _livery_from_rest(m.group(2))

    # 5e) Speisewagen / Grossraumwagen Ergänzung
    m = re.match(
        r"^(Speisewagen|Grossraumwagen)\b\s*,?\s*(.*)$",
        work,
        re.I,
    )
    if m:
        return m.group(1), None, _livery_from_rest(m.group(2))

    # 5f) Pantographen / Zubehör
    if re.search(r"(?i)fahrstromabnehmer|pantographe|\bPANTO\b", work) or re.search(
        r"(?i)^PANTO$", cat
    ):
        short = work.split(",")[0].strip()
        if len(short) > 60:
            short = short[:60].rstrip()
        return short, None, _livery_from_rest(work[len(short) :])

    # 5g) CIWL sleepers S1/S2/S3/SG/STU
    m = re.match(
        r"^((?:S1|S2|S3|SG|STU)(?:\s*\+\s*(?:S1|S2|S3|SG|STU))*)\b\s*,?\s*(.*)$",
        work,
        re.I,
    )
    if m and re.search(r"(?i)\bCIWL\b", work):
        return re.sub(r"\s+", " ", m.group(1).strip()), None, _livery_from_rest(m.group(2))

    # 6) Vectron / Smartron / BR ####
    m = re.match(
        r"^((?:Siemens\s+)?(?:Vectron|Smartron)(?:\s+MS)?|BR\s*\d{2,3})\b(.*)$",
        work,
        re.I,
    )
    if m:
        typ = re.sub(r"\s+", " ", m.group(1).strip())
        typ = re.sub(r"(?i)^br\s*", "BR ", typ)
        if re.search(r"(?i)vectron", typ) and not re.search(r"(?i)siemens", typ):
            typ = "Vectron MS" if re.search(r"(?i)\bMS\b", work) else "Vectron"
        rest = m.group(2).strip(" ,;-")
        # Operator often leads: «DB Cargo Vectron MS, …»
        return typ, None, _livery_from_rest(rest) if rest else None

    m = re.match(
        r"^(.+?)\s+((?:Siemens\s+)?(?:Vectron|Smartron)(?:\s+MS)?)\b(.*)$",
        work,
        re.I,
    )
    if m:
        typ = "Vectron MS" if re.search(r"(?i)\bMS\b", m.group(2)) else (
            "Smartron" if re.search(r"(?i)smartron", m.group(2)) else "Vectron"
        )
        # Leading token is operator (already handled separately); rest → livery
        rest = (m.group(3) or "").strip(" ,;-")
        quoted = re.search(r'[“"«]([^”"»]{2,60})[”"»]', work)
        liv = quoted.group(1).strip() if quoted else _livery_from_rest(rest)
        return typ, None, liv

    # 7) Passenger coaches / sleepers (Gattung first; keep type short)
    m = re.match(
        r"^("
        r"Apm(?:\s+EC)?(?:\s+Panorama)?|"
        r"Bpm(?:\s+EC)?|"
        r"Bcmz|WLABmz|WLABmee|WLSReem|"
        r"I10|I2|I5|I6|M6|OCEM(?:\s+[\w-]+)?"
        r")\b(.*)$",
        work,
        re.I,
    )
    if m:
        typ = re.sub(r"\s+", " ", m.group(1).strip())
        return typ, None, _livery_from_rest(m.group(2))

    # 8) CATEGORIE as type when title is long marketing and categorie is short class
    if cat and cat not in {"---", "-", "?"} and len(cat) <= 24 and len(work) > 40:
        if re.search(r"\b(?:HLE|BB|CC|VECTRON|AGC|X\s*\d)\b", cat, re.I):
            if re.match(r"(?i)^HLE\s*\d", cat):
                typ_cat = re.sub(r"(?i)^HLE\s*", "HLE ", cat).strip()
            else:
                typ_cat = cat
            return typ_cat, None, _livery_from_rest(work)

    return raw, None, None


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
    categorie = features.get("CATEGORIE") or ""
    operator, country = _operator_from_title(title, features.get("PAYS") or "")
    cats = _categories_from_materiel(
        features.get("TYPE DE MATERIEL") or "",
        categorie=categorie,
        title=title,
    )
    if cats == ["zubehoer"]:
        raise ValueError(f"{art}: Zubehör (Fahrstromabnehmer-Set), kein Rollmaterial")
    typ, number, livery = split_lsmodels_title(title, categorie=categorie)
    # SNCF BB/CC / Autorail X without PAYS/title operator → FR
    if operator == "Unbekannt" and re.match(
        r"^(?:BB|CC)\s+\d|^X\s+\d{3,4}\b|^AGC\b|^Vtu\b|^Gril\b",
        typ or "",
        re.I,
    ):
        operator, country = "SNCF", "FR"
    # Belgian HLE
    if operator == "Unbekannt" and re.match(r"^HLE\s+\d", typ or "", re.I):
        if re.search(r"\bLINEAS\b", title, re.I):
            operator, country = "LINEAS", "BE"
        else:
            operator, country = "SNCB", "BE"
    # DB ET / BR
    if operator == "Unbekannt" and re.match(
        r"^(?:ET\s*\d|BR\s*\d|E\s*\d{3}|Speisewagen|Grossraumwagen)",
        typ or "",
        re.I,
    ):
        operator, country = "DB", "DE"
    # SBB coaches
    if operator == "Unbekannt" and re.match(r"^(?:Apm|Bpm|EW\s*I)\b", typ or "", re.I):
        operator, country = "SBB", "CH"
    # SNCB I-coaches / M6
    if operator == "Unbekannt" and re.match(r"^(?:I[245610]|M6)\b", typ or "", re.I):
        operator, country = "SNCB", "BE"
    # CIWL
    if operator == "Unbekannt" and re.search(r"(?i)\bCIWL\b", title):
        operator, country = "CIWL", "FR"

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
        "type": typ or title or "Unbekannt",
        "number": number,
        "livery": livery,
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
