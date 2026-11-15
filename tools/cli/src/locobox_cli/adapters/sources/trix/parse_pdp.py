from __future__ import annotations

import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Optional

from locobox_cli.domain.text import swiss_ss

_OPERATOR_COUNTRY = {
    "DB AG": "DE",
    "DB": "DE",
    "DBG": "DE",
    "DRG": "DE",
    "DR": "DE",
    "SEL": "DE",
    "SBB": "CH",
    "ÖBB": "AT",
    "OBB": "AT",
    "RCG": "AT",
    "NS": "NL",
    "SNCF": "FR",
    "SNCB": "BE",
    "NMBS": "BE",
    "FS": "IT",
    "PKP": "PL",
    "ČSD": "CZ",
    "CSD": "CZ",
    "ČD": "CZ",
    "CD": "CZ",
    "DSB": "DK",
    "MAV": "HU",
    "SJ": "SE",
    "VR": "FI",
    "BLS": "CH",
    "CFL": "LU",
    "ELP": "CH",
}

_OPERATOR_ALIASES = {
    "DB-AG": "DB AG",
    "DBAG": "DB AG",
    "MÁV": "MAV",
    "ČD": "CD",
    "ČSD": "CSD",
    "SNCB/NMBS": "SNCB",
    "NMBS/SNCB": "SNCB",
}

_PAREN_OP = re.compile(
    r"\((?P<op>"
    + "|".join(
        sorted(
            (re.escape(k) for k in list(_OPERATOR_COUNTRY) + list(_OPERATOR_ALIASES)),
            key=len,
            reverse=True,
        )
    )
    + r")\)"
)

_SCALE_MAP = {
    "trix h0": "H0",
    "h0": "H0",
    "minitrix": "N",
    "n": "N",
    "1": "1",
    "spur 1": "1",
}


def _plain(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html_lib.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _spec_rows(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for mo in re.finditer(r"<tr[^>]*>[\s\S]*?</tr>", html, re.I):
        cells = [_plain(c) for c in re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", mo.group(0), re.I)]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            key = cells[0].rstrip(":").strip()
            val = cells[1].strip(" /").strip()
            if key and val and key not in out:
                out[key] = val
    return out


def _h1(html: str) -> str:
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
    return swiss_ss(_plain(m.group(1))) if m else ""


def _labeled_paragraphs(html: str) -> dict[str, str]:
    """Extract ``<b>Vorbild:</b> …</p>`` / ``<b>Modell:</b> …</p>`` product prose."""
    out: dict[str, str] = {}
    for mo in re.finditer(
        r"<b>\s*(Vorbild|Modell)\s*:</b>\s*([\s\S]*?)</p>",
        html,
        re.I,
    ):
        label = mo.group(1).strip().title()
        text = swiss_ss(_plain(mo.group(2)))
        if text and label not in out:
            out[label] = text
    return out


def _description(html: str, title: str) -> str:
    labeled = _labeled_paragraphs(html)
    parts = [f"{k}: {v}" for k, v in labeled.items() if v]
    if parts:
        return "\n\n".join(parts)
    return swiss_ss(title or "")


def _main_image(html: str) -> str:
    for m in re.finditer(r'src="(https://static\.maerklin\.de/[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html, re.I):
        return m.group(1).split("?")[0]
    return ""


def _normalize_scale(raw: str) -> str:
    key = raw.strip().lower()
    for needle, scale in _SCALE_MAP.items():
        if needle in key:
            return scale
    if "h0" in key or "hö" in key:
        return "H0"
    return "H0"


def _electric(html: str, description: str) -> str:
    blob = f"{html} {description}".lower()
    digital = any(
        x in blob
        for x in (
            "digital-decoder",
            "digitaldecoder",
            "mfx",
            "dcc",
            "sound",
            "geräuschfunktion",
        )
    )
    # Trix H0 / Minitrix are DC (2-rail); Märklin AC is a different brand line.
    return "DC-Digital" if digital else "DC-Analog"


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


def _operator_from_vorbild(description: str) -> tuple[str, str]:
    # Disambiguate before generic (NS) → NL mapping.
    if re.search(r"Norfolk\s+Southern", description, re.I):
        return "NS", "US"
    if re.search(r"Rail Cargo Group|\bRCG\b", description, re.I):
        return "RCG", "AT"
    m = _PAREN_OP.search(description)
    if m:
        return _operator_country(m.group("op"))
    # «der Deutschen Bundesbahn» without parentheses
    if re.search(r"Deutschen?\s+Bahn\s+Gleisbau|\bDBG\b", description, re.I):
        return "DBG", "DE"
    if re.search(r"DB\s+Bahnbau", description, re.I):
        return "DB", "DE"
    if re.search(r"Schlünss|Schluenss|\bSEL\b", description, re.I):
        return "SEL", "DE"
    if re.search(r"European Loc Pool|\bELP\b", description, re.I):
        return "ELP", "CH"
    if re.search(r"Belgischen?\s+Staatsbahn|SNCB|NMBS", description, re.I):
        return "SNCB", "BE"
    if re.search(r"Deutschen?\s+Bundesbahn", description, re.I):
        return "DB", "DE"
    if re.search(r"Deutschen?\s+Reichsbahn", description, re.I):
        return "DR", "DE"
    if re.search(r"Schweizerischen?\s+Bundesbahnen", description, re.I):
        return "SBB", "CH"
    return "Unbekannt", "DE"


def _luep_mm(html: str, description: str) -> Optional[float]:
    blob = f"{html} {description}"
    m = re.search(
        r"Länge\s+über\s+Puffer\s+(?:ca\.\s*)?(\d+(?:[.,]\d+)?)\s*cm",
        blob,
        re.I,
    )
    if not m:
        return None
    cm = float(m.group(1).replace(",", "."))
    return round(cm * 10, 1)


def _min_radius_mm(html: str, description: str) -> Optional[float]:
    blob = f"{html} {description}"
    m = re.search(r"(?:Mindestradius|Radius)\s+(\d+(?:[.,]\d+)?)\s*mm", blob, re.I)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def parse_trix_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    specs = _spec_rows(html)
    shop_article = (specs.get("Art.Nr.") or specs.get("Art. Nr.") or "").strip() or article.strip()
    if shop_article != article.strip():
        raise ValueError(f"product article {shop_article} != requested {article}")

    title = _h1(html) or swiss_ss(article)
    desc = _description(html, title)
    era = (specs.get("Epoche") or "Unbekannt").strip() or "Unbekannt"
    scale = _normalize_scale(specs.get("Spur / Bauart") or specs.get("Spur") or "Trix H0")
    operator, country = _operator_from_vorbild(desc)
    electric = _electric(html, desc)
    img = _main_image(html)
    luep = _luep_mm(html, desc)
    min_r = _min_radius_mm(html, desc)

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
    if luep is not None:
        model["luepMm"] = luep
    if min_r is not None:
        model["minRadiusMm"] = min_r

    tags: list[str] = []
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
    release = None
    if campaign_tag:
        m = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if m:
            release = m.group(1)

    amount = float(uvp_amount) if uvp_amount is not None else 0.0
    source: dict[str, Any] = {
        "url": canonical_url,
        "notes": "Daten von der Trix-Produktdatenbank, automatisch geupdated.",
    }
    if img.startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"trix-{shop_article}",
        "manufacturer": "Trix",
        "articleNumber": shop_article,
        "releaseDate": release,
        "uvp": {"amount": amount, "currency": "EUR"},
        "model": model,
        "description": desc,
        "categories": ["lokomotive"],
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
