from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# Canonical SKU: HJ2461 / HJ2461S. Catalogs also write HJ2461/HJ2461S or HJ2461/S.
# Negative lookaround avoids eating HJ4206 out of HJ4206HM / HJ4176-1.
_SKU = re.compile(
    r"(?<![A-Za-z0-9])HJ(?P<digits>\d{4})(?P<sound>S)?(?![A-Za-z0-9])",
    re.I,
)
_PAIR_SLASH_S = re.compile(
    r"(?<![A-Za-z0-9])HJ(?P<digits>\d{4})\s*/\s*S(?![A-Za-z0-9])",
    re.I,
)

_SECTION_LOCO = re.compile(
    r"Locomotives?\s+(?:à\s+vapeur|diesel|électriques?)|"
    r"Steam\s+locomotives?|Diesel\s+locomotives?|Electric\s+locomotives?|"
    r"Dampflokomotiven|Diesellokomotiven|Elektrolokomotiven|"
    r"Materiel\s+moteur|Matériel\s+moteur",
    re.I,
)
_SECTION_COACH = re.compile(
    r"\bVoitures\b|\bCoaches\b|Personenwagen|Locomotives?\s+loisirs|"
    r"Jouef\s+Loisirs",
    re.I,
)
_SECTION_WAGON = re.compile(r"\bWagons\b|Güterwagen", re.I)
_SECTION_OTHER = re.compile(
    r"\bVoies\b|\bTracks\b|Accessoires|Accessories|Bâtiments|Buildings|"
    r"MKD|Still\s+available|Arrivées\s+récentes",
    re.I,
)

_KIND_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"vapeur|steam|dampf", re.I), "Dampflok"),
    (re.compile(r"diesel|autorail|triebwagen|railcar", re.I), "Diesellok"),
    (re.compile(r"électri|electri|elektro", re.I), "Elektrolok"),
]


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def _kind_for_section(section: str, context: str, loco_kind: str) -> str:
    if section == "coach":
        return "Personenwagen"
    if section == "wagon":
        return "Güterwagen"
    if section == "other":
        return "Rollendes Material"
    for pat, kind in _KIND_HINTS:
        if pat.search(context):
            return kind
    return loco_kind


def _loco_kind_from_header(line: str) -> Optional[str]:
    for pat, kind in _KIND_HINTS:
        if pat.search(line):
            return kind
    if re.search(r"Materiel\s+moteur|Matériel\s+moteur", line, re.I):
        return "Lokomotive"
    return None


def _iter_skus(line: str) -> list[str]:
    """Yield canonical HJ#### / HJ####S from one catalog line."""
    found: list[str] = []
    seen: set[str] = set()

    def add(sku: str) -> None:
        if sku not in seen:
            seen.add(sku)
            found.append(sku)

    for m in _PAIR_SLASH_S.finditer(line):
        digits = m.group("digits")
        add(f"HJ{digits}")
        add(f"HJ{digits}S")

    for m in _SKU.finditer(line):
        digits = m.group("digits")
        sound = (m.group("sound") or "").upper()
        add(f"HJ{digits}{sound}")
        # HJ2461/HJ2461S already yields both via separate matches.
        # Shorthand HJ2461/S handled above.

    return found


def extract_jouef_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract Jouef ``HJ####`` / ``HJ####S`` SKUs from ``pdftotext -layout`` output.

    Tracks coarse section headers (loco / coach / wagon). With
    ``locomotives_only`` (default), coach/wagon/other sections are skipped.
    Prices are usually absent in Jouef PDF text; ``price_eur`` stays ``None``.
    """
    raw = [_norm(line) for line in text.splitlines()]
    section = "locomotive"
    loco_kind = "Lokomotive"
    rows: list[CatalogRow] = []
    seen: set[str] = set()

    for i, line in enumerate(raw):
        stripped = line.strip()
        if not stripped:
            continue
        if len(stripped) < 120:
            if _SECTION_LOCO.search(stripped):
                section = "locomotive"
                loco_kind = _loco_kind_from_header(stripped) or loco_kind
            elif _SECTION_COACH.search(stripped):
                section = "coach"
            elif _SECTION_WAGON.search(stripped):
                section = "wagon"
            elif _SECTION_OTHER.search(stripped):
                section = "other"

        if locomotives_only and section != "locomotive":
            continue

        context = " ".join(
            x.strip()
            for x in (raw[i - 1] if i >= 1 else "", line, raw[i + 1] if i + 1 < len(raw) else "")
            if x.strip()
        )[-500:]
        for sku in _iter_skus(stripped):
            if sku in seen:
                continue
            seen.add(sku)
            rows.append(
                CatalogRow(
                    article=sku,
                    price_eur=None,
                    section=section,
                    kind=_kind_for_section(section, context, loco_kind),
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
        # Jouef catalog text usually has no prices; keep unknown UVP.
        filtered = [
            r for r in rows if r.price_eur is None or r.price_eur > min_price_eur
        ]
    headers = [
        f"# Jouef catalog extract ({len(filtered)} articles"
        + (f", UVP > {min_price_eur:g} EUR or unknown" if min_price_eur is not None else "")
        + "; prices usually from shop)"
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
