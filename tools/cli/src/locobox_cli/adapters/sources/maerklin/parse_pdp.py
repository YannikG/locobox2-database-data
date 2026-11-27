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
    "GYSEV": "HU",
    "MRCE": "DE",
    "ERS": "NL",
    "UP": "US",
    "PRR": "US",
    "ATSF": "US",
    "NSB": "NO",
    "SOB": "CH",
    "ZSSK": "SK",
    "KPEV": "DE",
    "Hector Rail": "SE",
    "Railpool": "DE",
    "ELL": "AT",
    "DB Cargo": "DE",
    "DB Schenker": "DE",
    "SBB Cargo": "CH",
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
    r"\(\s*(?P<op>"
    + "|".join(
        sorted(
            (re.escape(k) for k in list(_OPERATOR_COUNTRY) + list(_OPERATOR_ALIASES)),
            key=len,
            reverse=True,
        )
    )
    + r")\s*\)"
)

_SCALE_MAP = {
    "märklin h0": "H0",
    "maerklin h0": "H0",
    "h0": "H0",
    "spur z": "Z",
    "z": "Z",
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
    for m in re.finditer(
        r'src="(https://static\.maerklin\.de/[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        html,
        re.I,
    ):
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
            "gerauschfunktion",
        )
    )
    # Märklin H0 is AC (3-rail); Trix DC is a different brand line.
    return "AC-Digital" if digital else "AC-Analog"


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
    """Map Vorbild prose / parenthetical codes to operator + ISO country."""
    # Named US roads before bare «NS» (Norfolk Southern vs. Nederlandse Spoorwegen).
    if re.search(r"Norfolk\s+Southern", description, re.I):
        return "NS", "US"
    if re.search(r"Union\s+Pacific|\bU\.?P\.?\b", description, re.I):
        return "UP", "US"
    if re.search(r"Pennsylvania\s+Railroad|\bPRR\b", description, re.I):
        return "PRR", "US"
    if re.search(r"Atchison|Santa\s+Fe|\bA\.?\s*T\.?\s*&?\s*S\.?\s*F\.?\b", description, re.I):
        return "ATSF", "US"
    if re.search(r"Rail Cargo Group|\bRCG\b", description, re.I):
        return "RCG", "AT"
    m = _PAREN_OP.search(description)
    if m:
        return _operator_country(m.group("op"))
    # Free-text EVU / Bahnverwaltung (ordered: specific before generic DB/SBB).
    text_ops: list[tuple[str, str, str]] = [
        (r"Hector\s*Rail", "Hector Rail", "SE"),
        (r"Mitsui\s+Rail\s+Capital|\bMRCE\b", "MRCE", "DE"),
        (r"\bRailpool\b", "Railpool", "DE"),
        (r"\bELL\b", "ELL", "AT"),
        (r"DB\s+Schenker", "DB Schenker", "DE"),
        (r"DB\s+Cargo", "DB Cargo", "DE"),
        (r"SBB\s+Cargo", "SBB Cargo", "CH"),
        (r"BLS\s+Cargo|\bBLS\b", "BLS", "CH"),
        (r"Südostbahn|\bSOB\b", "SOB", "CH"),
        (r"Schweizer\s+Südostbahn", "SOB", "CH"),
        (r"Železni[cč]n[aá]\s+spolo[cč]nos[tť]|\bZSSK\b|ŽSSK", "ZSSK", "SK"),
        (r"Tschechischen?\s+Staatsbahn|\bČD\b|\bCD\b(?!\s*Cargo)", "CD", "CZ"),
        (r"Norwegischen?\s+Staatsbahn|\bNSB\b", "NSB", "NO"),
        (r"K\.?\s*P\.?\s*E\.?\s*V\.?|Königlich\s+Preussischen?\s+Eisenbahn", "KPEV", "DE"),
        (r"K\.?\s*Bay\.?\s*Sts\.?\s*B\.?|Königlich\s+Bayerischen?\s+Staats", "K.Bay.Sts.B.", "DE"),
        (r"K\.?\s*W\.?\s*St\.?\s*E\.?|Württembergischen?\s+Staatseisenbahn", "K.W.St.E.", "DE"),
        (r"W\.?\s*St\.?\s*E\.?", "W.St.E.", "DE"),
        (r"Französischen?\s+Ostbahn|\bEST\b", "EST", "FR"),
        (r"Euro\s+Cargo\s+Rail|\bECR\b", "ECR", "DE"),
        (r"CTL\s+Logistics", "CTL Logistics", "PL"),
        (r"Mercitalia", "Mercitalia", "IT"),
        (r"CFL\s+Cargo|\bCFL\b", "CFL", "LU"),
        (r"LINEAS", "LINEAS", "BE"),
        (r"Crossrail", "Crossrail", "CH"),
        (r"Strukton", "Strukton", "NL"),
        (r"CargoNet", "CargoNet", "NO"),
        (r"RushRail", "RushRail", "SE"),
        (r"Rotterdam\s+Rail\s+Feeding|\bRRF\b", "RRF", "NL"),
        (r"Häfen\s+und\s+Güterverkehr\s+Köln|\bHGK\b", "HGK", "DE"),
        (r"Lokomotion", "Lokomotion", "DE"),
        (r"Swiss\s+Rail\s+Traffic", "Swiss Rail Traffic", "CH"),
        (r"Colas\s+Rail", "Colas Rail", "FR"),
        (r"Bergslagernas|\bBJ\b", "BJ", "SE"),
        (r"Amtrak", "Amtrak", "US"),
        (r"Deutschen?\s+Bahn\s+Gleisbau|\bDBG\b", "DBG", "DE"),
        (r"DB\s+Bahnbau", "DB", "DE"),
        (r"Schlünss|Schluenss|\bSEL\b", "SEL", "DE"),
        (r"European\s+Loc\s+Pool|\bELP\b", "ELP", "CH"),
        (r"Belgischen?\s+Staatsbahn|SNCB|NMBS", "SNCB", "BE"),
        (r"Österreichischen?\s+Bundesbahn|\bÖBB\b|\bOBB\b", "ÖBB", "AT"),
        (r"Deutschen?\s+Bahn\s+AG|\bDB\s+AG\b", "DB AG", "DE"),
        (r"Deutschen?\s+Bundesbahn", "DB", "DE"),
        (r"Deutschen?\s+Reichsbahn", "DR", "DE"),
        (r"Schweizerischen?\s+Bundesbahn|\bSBB\b", "SBB", "CH"),
        (r"Niederländischen?\s+Eisenbahn|\bNS\b(?!\s+Southern)", "NS", "NL"),
        (r"Polnischen?\s+Staatsbahn|\bPKP\b", "PKP", "PL"),
        (r"Italienischen?\s+Staatsbahn|\bFS\b", "FS", "IT"),
        (r"Französischen?\s+Staatsbahn|\bSNCF\b", "SNCF", "FR"),
    ]
    for pat, op, cc in text_ops:
        if re.search(pat, description, re.I):
            return op, cc
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


_GENERIC_PRODUCT_TYPE = re.compile(
    r"^(?:Märklin\s+Start\s+up\s*-\s*)?(?:Schlepptender-)?"
    r"(?:Dampf|Diesel|Elektro|Zweikraft)lokomotive$",
    re.I,
)

_MULTI_UNIT = re.compile(
    r"Triebzug|Triebwagenzug|Triebwagen-Zug|Hochgeschwindigkeits|Gliedertriebzug|\bICE\b|\bTGV\b",
    re.I,
)
_RAILCAR = re.compile(r"Triebwagen|Schienenbus|Schienenomnibus|Steuerwagen|Regio\s*Shuttle", re.I)
_GENERIC_RAILCAR_TYPE = re.compile(
    r"^(?:[\w\-]+[\- ])?(?:Elektro|Diesel|Akku|Nahverkehrs-?|S-Bahn[- ]?)?"
    r"(?:triebwagen|triebzug|triebwagenzug|schienenbus|schienenomnibus)\.?$",
    re.I,
)


_CLASS_ONLY = re.compile(
    r"^(?:(?:Schnellzug|Personenzug|Güterzug|Schwere|Schwerer?|Stromlinien|Rangier|Erz|Weihnachts|"
    r"Schlepptender|Mehrzweck|Aussichts)[- ]?)*"
    r"(?:Dampf|Diesel|Elektro|Tender|Schnellzug|Güterzug|Personenzug|Rangier|Erz|Zweikraft|Gelenk|Kleinlok)?"
    r"-?(?:klein)?(?:lokomotive|lok|triebwagen|schnelltriebwagen|triebzug)"
    r"(?:\s+mit\s+[\w\- ]*(?:tender|Steuerwagen))?$",
    re.I,
)


def _is_generic_class_title(t: str) -> bool:
    """Title is only a product class (no Baureihe/number), e.g. «Schnellzug-Dampflokomotive mit Schlepptender»."""
    if re.fullmatch(r"mit\s+[\w\- ]*tender", t, re.I):
        return True
    return bool(t) and not re.search(r"\d", t) and bool(_CLASS_ONLY.fullmatch(t))


def _categories(title: str, description: str) -> list[str]:
    """Parent + sub categories. Lok sub-types (dampf/diesel/elektro) come from autofix."""
    head = f"{title} {description.split('Modell:', 1)[0]}"
    if _MULTI_UNIT.search(title) or _MULTI_UNIT.search(head[:200]):
        base = "triebzug"
    elif _RAILCAR.search(title):
        base = "triebwagen"
    else:
        out = ["lokomotive"]
        low = f"{title} {description.split('Modell:', 1)[0][:240]}".lower()
        if re.search(r"dampf|tenderlok|schlepptender|wannentender", low):
            out.append("dampflokomotive")
        elif re.search(r"diesel|dieselhydraul|köf", low):
            out.append("diesellokomotive")
        elif re.search(r"elektro|elektrisch|e-lok", low):
            out.append("elektrolokomotive")
        return out
    out = [base]
    low = head.lower()
    if re.search(r"akku", low):
        out.append("akkutriebwagen")
    elif re.search(r"diesel|vt\b|schienenbus|schienenomnibus|lint|regio\s*shuttle", low):
        out.append("dieseltriebwagen")
    elif re.search(r"elektr|\bet\b|\bice\b|\btgv\b|desiro|s-bahn", low):
        out.append("elektrotriebwagen")
    return out


def _type_from_title_or_vorbild(title: str, description: str) -> str:
    t = swiss_ss((title or "").strip())
    t_plain = t.rstrip(". ").strip()
    if t and not (
        _GENERIC_PRODUCT_TYPE.fullmatch(t_plain)
        or _GENERIC_RAILCAR_TYPE.fullmatch(t_plain)
        or _is_generic_class_title(t_plain)
    ):
        return t
    vor = ""
    if description:
        vor = description.split("Modell:", 1)[0]
        vor = re.sub(r"^Vorbild:\s*", "", vor, flags=re.I).strip()
    if not vor:
        return t or "Unbekannt"
    first = re.split(r"(?<=\.)\s+", vor, maxsplit=1)[0].strip()
    # Prefer «Baureihe …» / «Serie …» / «Reihe …» fragment when present.
    m = re.search(
        r"((?:Baureihe|Serie|Reihe|Typ|Class|Rh|BR)\s+.+?)"
        r"(?=\s+(?:der|des|von|mit|in|als|aus|und)\b|[.,;]|$)",
        first,
        re.I,
    )
    if m:
        return swiss_ss(m.group(1).strip())
    # Else strip leading product-word fluff: «Elektrolokomotive Baureihe …»
    stripped = re.sub(
        r"^(?:Schlepptender-)?(?:Dampf|Diesel|Elektro|Zweikraft|Dieselelektrische|"
        r"Schwere(?:\s+Mehrzweck)?|Mehrzweck)(?:e)?(?:lokomotive|Lokomotive)?\s+",
        "",
        first,
        flags=re.I,
    ).strip()
    stripped = re.split(
        r"\s+(?:der|des|von|mit|in|als|aus|und)\b",
        stripped,
        maxsplit=1,
        flags=re.I,
    )[0].strip(" ,;-")
    return swiss_ss(stripped or first or t or "Unbekannt")


def parse_maerklin_pdp(
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
    scale = _normalize_scale(specs.get("Spur / Bauart") or specs.get("Spur") or "H0")
    operator, country = _operator_from_vorbild(desc)
    electric = _electric(html, desc)
    img = _main_image(html)
    luep = _luep_mm(html, desc)
    min_r = _min_radius_mm(html, desc)
    model_type = _type_from_title_or_vorbild(title, desc)

    model: dict[str, Any] = {
        "country": country,
        "operator": operator,
        "type": model_type,
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
        "notes": "Daten von der Märklin-Produktdatenbank, automatisch geupdated.",
    }
    if img.startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"maerklin-{shop_article}",
        "manufacturer": "Maerklin",
        "articleNumber": shop_article,
        "releaseDate": release,
        "uvp": {"amount": amount, "currency": "EUR"},
        "model": model,
        "description": desc,
        "categories": _categories(title, desc),
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
