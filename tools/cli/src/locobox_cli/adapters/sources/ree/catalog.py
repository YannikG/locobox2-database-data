from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# Motorized / first-slice prefixes (locos, TGV, Access JM, optional HOm VM).
_MOTORIZED_PREFIXES = frozenset({"MB", "TGV", "JM", "VM"})
# Rolling stock / other families skipped when locomotives_only.
_WAGON_PREFIXES = frozenset({"VB", "WB", "NW", "CB"})

# Catalogue / site lines: «Réf. MB-263», «Réf. TGV-004 S», «Ref. JM-001»
_REF_LINE = re.compile(
    r"(?:R[eé]f\.?\s*)"
    r"(?P<raw>"
    r"(?P<prefix>MB|TGV|JM|VM|VB|WB|NW|CB)"
    r"[-\s]?(?P<digits>\d{1,6})"
    r"(?:[-\s]?(?P<suffix>SAC|S))?"
    r")\b",
    re.I,
)
# Bare refs sometimes appear without Réf. (PDF columns / indexes).
_BARE_REF = re.compile(
    r"(?<![A-Za-z0-9-])"
    r"(?P<raw>"
    r"(?P<prefix>MB|TGV|JM|VM)"
    r"[-\s]?(?P<digits>\d{1,6})"
    r"(?:[-\s]?(?P<suffix>SAC|S))?"
    r")\b",
    re.I,
)

_PRICE = re.compile(
    r"(?P<price>(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})\s*(?:€|EUR)?",
    re.I,
)


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


def _parse_price(raw: str) -> float:
    s = re.sub(r"\.(?=\d{3},)", "", raw.strip()).replace(",", ".")
    return float(s)


def _kind_from_context(prefix: str, context: str) -> str:
    p = prefix.upper()
    ctx = context.lower()
    if p == "TGV":
        return "Triebzug"
    if p == "JM":
        return "Zubehör"
    if p == "VM":
        return "Lokomotive"
    if re.search(r"autorail|triebwagen|rgp\b", ctx, re.I):
        return "Triebwagen"
    if re.search(r"vapeur|dampf", ctx, re.I):
        return "Dampflok"
    if re.search(r"diesel", ctx, re.I):
        return "Diesellok"
    if re.search(r"électrique|electrique|elektro", ctx, re.I):
        return "Elektrolok"
    if re.search(r"locomotive|lokomotive|\blok\b", ctx, re.I):
        return "Lokomotive"
    return "Lokomotive"


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def _canonical_from_match(m: re.Match[str]) -> Optional[str]:
    prefix = m.group("prefix").upper()
    digits = m.group("digits")
    suffix = (m.group("suffix") or "").upper()
    raw = f"{prefix}-{digits}{suffix}"
    try:
        return ArticleNumber.parse(raw).value
    except ValueError:
        return None


def extract_ree_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract REE catalog refs from ``pdftotext -layout`` / catalogue text.

    First slice focuses on motorized stock (MB / TGV / JM / VM). With
    ``locomotives_only`` (default), wagon families (VB / WB / NW / CB) are skipped.
    Prices are optional (many catalogue pages omit UVP).
    """
    raw = [_norm(line) for line in text.splitlines()]
    rows: list[CatalogRow] = []
    seen: set[str] = set()

    for i, line in enumerate(raw):
        stripped = line.strip()
        if not stripped:
            continue
        context = " ".join(
            x.strip()
            for j in range(max(0, i - 3), min(len(raw), i + 2))
            for x in (raw[j],)
            if x.strip()
        )[-500:]
        price: Optional[float] = None
        pm = _PRICE.search(stripped)
        if pm:
            try:
                price = _parse_price(pm.group("price"))
            except ValueError:
                price = None

        matches = list(_REF_LINE.finditer(stripped))
        if not matches:
            matches = list(_BARE_REF.finditer(stripped))
        for m in matches:
            prefix = m.group("prefix").upper()
            if locomotives_only and prefix in _WAGON_PREFIXES:
                continue
            if locomotives_only and prefix not in _MOTORIZED_PREFIXES:
                continue
            if not locomotives_only and prefix not in (_MOTORIZED_PREFIXES | _WAGON_PREFIXES):
                continue
            art = _canonical_from_match(m)
            if not art or art in seen:
                continue
            seen.add(art)
            rows.append(
                CatalogRow(
                    article=art,
                    price_eur=price,
                    section="motorized" if prefix in _MOTORIZED_PREFIXES else "rolling",
                    kind=_kind_from_context(prefix, context),
                    line_context=stripped[:240],
                )
            )

    rows.sort(key=lambda r: (r.section, r.article, r.kind))
    return rows


def rows_to_queue(
    rows: list[CatalogRow],
    *,
    min_price_eur: Optional[float] = None,
) -> QueueDocument:
    filtered = rows
    if min_price_eur is not None:
        filtered = [
            r for r in rows if r.price_eur is None or r.price_eur > min_price_eur
        ]
    headers = [
        f"# REE catalog extract ({len(filtered)} articles"
        + (
            f", UVP > {min_price_eur:g} EUR or unknown"
            if min_price_eur is not None
            else ""
        )
        + "; motorized MB/TGV/JM/VM)"
    ]
    entries = [
        QueueEntry(
            article=ArticleNumber(r.article),
            kind=r.kind,
            section=r.section,
            price_eur=r.price_eur,
        )
        for r in filtered
    ]
    return QueueDocument(entries=entries, header_comments=headers)
