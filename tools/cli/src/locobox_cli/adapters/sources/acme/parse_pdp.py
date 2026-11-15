from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

from locobox_cli.domain.text import swiss_ss

_SKU = re.compile(r"(?<![A-Za-z0-9])(?:AC)?(?P<sku>\d{5})(?!\d)", re.I)
_SKU_PRICE = re.compile(
    r"(?<![A-Za-z0-9])(?:AC)?(?P<sku>\d{5})(?!\d)\s+(?P<price>\d{2,4})\b",
    re.I,
)
_DE_DESC = re.compile(
    r"^\s*(?P<body>(?:Lokomotive|Elektrolokomotive|Diesellokomotive|Dampflokomotive)\b.+)$",
    re.I,
)
_IT_LOCO_TITLE = re.compile(
    r"^\s*(?P<title>Locomotiva(?:\s+(?:elettrica|diesel|a\s+vapore))?)\b",
    re.I,
)
_MODEL_HEAD = re.compile(
    r"^\s*(?P<head>(?:SBB|FS|DB|ÖBB|MAV|MÁV|TRAXX|Re\s*\d+|E\.?\d+|BR\s*\d+)[^\n]{0,80})$",
    re.I,
)


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


def _guess_operator_country(text: str) -> tuple[str, str]:
    t = text.lower()
    if "sbb" in t or "zürich" in t or "zurich" in t or "sihltal" in t:
        return "SBB", "CH"
    if re.search(r"\bfs\b", t) or "trenitalia" in t or "ferrovie dello stato" in t:
        return "FS", "IT"
    if re.search(r"\bdb\b", t) or "deutsche bahn" in t:
        return "DB", "DE"
    if "öbb" in t or "oebb" in t:
        return "ÖBB", "AT"
    if "railpool" in t:
        return "Railpool", "DE"
    if "akiem" in t:
        return "Akiem", "FR"
    if "medway" in t:
        return "Medway", "IT"
    return "Unbekannt", "IT"


def _model_type(lines: list[str], article: str) -> str:
    for line in lines[:12]:
        s = line.strip()
        if not s or len(s) > 80:
            continue
        if _IT_LOCO_TITLE.match(s):
            continue
        if _SKU.search(s) and len(s) < 40:
            continue
        if re.search(r"esclusiva|exclusive|exclusiv|acme s\.r\.l", s, re.I):
            continue
        if _MODEL_HEAD.match(s) or re.search(
            r"\b(?:Re\s*\d+|E\.?\s*\d+|TRAXX|BR\s*\d+)\b", s, re.I
        ):
            return _norm(s)[:120]
    return f"ACME {article}"


def _german_description(lines: list[str]) -> str:
    chunks: list[str] = []
    i = 0
    while i < len(lines):
        m = _DE_DESC.match(lines[i])
        if not m:
            i += 1
            continue
        parts = [m.group("body").strip()]
        j = i + 1
        # Soft-wrapped flyer lines (often after a hyphen at EOL).
        while j < len(lines):
            nxt = lines[j].strip()
            if not nxt:
                break
            if _DE_DESC.match(nxt) or _IT_LOCO_TITLE.match(nxt):
                break
            if re.search(r"acme s\.r\.l|esclusiva|exclusive|exclusiv", nxt, re.I):
                break
            if _SKU.search(nxt) and len(nxt) < 40:
                break
            parts.append(nxt)
            j += 1
            if not parts[-2].endswith("-") and len(nxt) > 80:
                break
        merged = parts[0]
        for p in parts[1:]:
            if merged.endswith("-"):
                # Syllable wrap (next lower-case) drops the hyphen; compounds keep it.
                if p[:1].islower():
                    merged = merged[:-1] + p
                else:
                    merged = merged + p
            else:
                merged = f"{merged} {p}"
        chunks.append(_norm(merged))
        i = j
    if chunks:
        return " ".join(chunks)
    for line in reversed(lines):
        s = line.strip()
        if len(s) < 40:
            continue
        if re.search(r"\b(Lokomotive|Lackierung|für den|Einsatz)\b", s, re.I):
            return _norm(s)
    return ""


def _uvp_for_article(text: str, article: str) -> float:
    art = article.strip()
    for m in _SKU_PRICE.finditer(text):
        if m.group("sku") == art:
            return float(m.group("price"))
    # Sibling DC SKU on same flyer often carries the printed UVP.
    if art.startswith("69"):
        dc = "60" + art[2:]
        for m in _SKU_PRICE.finditer(text):
            if m.group("sku") == dc:
                return float(m.group("price"))
    return 0.0


def _electric_system(article: str, text: str) -> str:
    del text  # page may mention exclusive AC/Sound siblings; SKU family decides
    # Schema: DC-Analog | DC-Digital | AC-Analog | AC-Digital | …
    if article.startswith("69"):
        return "DC-Digital"
    return "DC-Analog"


def parse_acme_flyer(
    text: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    """
    Parse ACME flyer ``pdftotext -layout`` output into article JSON.

    ACME has no HTML PDP; product sheets are PDFs under
    ``https://www.acmetreni.it/files/AC{article}.pdf``.
    """
    art = article.strip()
    if art.upper().startswith("AC") and art[2:].isdigit():
        art = art[2:]

    raw_lines = [_norm(line) for line in text.splitlines()]
    lines = [ln for ln in raw_lines if ln.strip()]
    joined = "\n".join(lines)

    if art not in {m.group("sku") for m in _SKU.finditer(joined)} and art not in joined:
        # Sound SKU may only appear as bare digits; still require presence.
        if not re.search(rf"(?<!\d){re.escape(art)}(?!\d)", joined):
            raise ValueError(f"flyer text does not mention article {art}")

    desc = _german_description(raw_lines)
    if not desc:
        # Prefer Italian body if DE missing.
        for line in raw_lines:
            s = line.strip()
            if s.lower().startswith("locomotiva ") and len(s) > 40:
                desc = _norm(s)
                break
    if not desc:
        desc = _norm(_model_type(lines, art))

    operator, country = _guess_operator_country(joined)
    model_type = _model_type(lines, art)
    amount = float(uvp_amount) if uvp_amount is not None else _uvp_for_article(joined, art)

    tags: list[str] = []
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
    release = None
    if campaign_tag:
        m = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if m:
            release = m.group(1)

    return {
        "schemaVersion": "1.0.0",
        "id": f"acme-{art}",
        "manufacturer": "ACME",
        "articleNumber": art,
        "releaseDate": release,
        "uvp": {"amount": amount, "currency": "EUR"},
        "model": {
            "country": country,
            "operator": operator,
            "type": model_type,
            "number": None,
            "livery": None,
            "scale": "H0",
            "electricSystem": _electric_system(art, joined),
            "era": "Unbekannt",
        },
        "description": desc,
        "categories": ["lokomotive"],
        "tags": tags,
        "source": {
            "url": canonical_url,
            "notes": "Daten aus ACME-Flyer-PDF (pdftotext), automatisch geparsed.",
        },
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def parse_acme_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    """
    ACME entry point used by ``shop parse``.

    Accepts flyer plain text (from ``pdftotext``). HTML PDPs do not exist;
    if the payload looks like HTML markup without flyer SKUs, raise clearly.
    """
    stripped = html.lstrip().lower()
    looks_html = stripped.startswith("<!doctype html") or stripped.startswith("<html")
    if looks_html:
        raise NotImplementedError(
            f"ACME PDP parse needs flyer text for article {article!r}: "
            "there is no stable HTML shop page; use "
            f"https://www.acmetreni.it/files/AC{article}.pdf with pdftotext."
        )
    return parse_acme_flyer(
        html,
        canonical_url=canonical_url,
        article=article,
        campaign_tag=campaign_tag,
        uvp_amount=uvp_amount,
    )
