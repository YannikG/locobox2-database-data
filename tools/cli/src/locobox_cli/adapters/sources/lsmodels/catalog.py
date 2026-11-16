from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# Catalog rows like: 16 075 / 16 575 / 16 075 S / 16 575 S  (DC / AC / Sound)
_SKU_TOKEN = re.compile(
    r"(?<![\w])(?P<a>\d{2})\s+(?P<b>\d{3})(?P<sound>\s*S)?(?![\w])",
    re.I,
)
_MW_TOKEN = re.compile(r"\bMW[\s-]?\d+", re.I)

_SECTION_LOCO = re.compile(
    r"^\s*(?:H0\s+)?"
    r"(Dampflokomotiven|Elektrolokomotiven|Diesellokomotiven|"
    r"Lokomotiven|Locomotives|"
    r"Dampf-\s*&\s*Elektrolokomotiven)"
    r"(?:\s*/\s*.{0,80})?\s*$",
    re.I,
)
_SECTION_OTHER = re.compile(
    r"^\s*(?:H0\s+)?"
    r"(Personenwagen|Güterwagen|Reisezugwagen|Wagons?|Voitures?|"
    r"Startsets|Zubehör|Accessoires|Impressum)"
    r"(?:\s*/\s*.{0,80})?\s*$",
    re.I,
)
_TITLE_LOCO = re.compile(
    r"^\s*.{0,40}\b(?:Dampf|Diesel|Elektro)?lokomotive\b"
    r"|^.{0,60}\b(?:Vectron|Traxx|Taurus|Re\s*\d|BR\s*\d)\b",
    re.I,
)
_TITLE_NON_LOCO = re.compile(
    r"^\s*(?:(?:\d+-tlg\.\s+)?(?:Set|Wagenset|Zugset)\b|"
    r"(?:Personenwagen|Güterwagen|Reisezugwagen|Voiture|Wagon)\b)",
    re.I,
)


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def extract_lsmodels_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract LS Models Neuheiten SKUs from ``pdftotext -layout`` output.

    Canonical numbers strip internal spaces (``16 075`` → ``16075``).
    Sound variants (``… S``) and Models-World ``MW…`` are skipped for now.
    Catalog PDFs typically omit UVP; ``price_eur`` is ``None``.
    """
    raw = [_norm(line) for line in text.splitlines()]
    section = "none"
    product = "unknown"  # loco | nonloco | unknown
    kind = "Lokomotive"
    title = ""
    rows: list[CatalogRow] = []
    seen: set[str] = set()

    for line in raw:
        stripped = line.strip()
        if not stripped:
            continue
        if _MW_TOKEN.search(stripped) and not _SKU_TOKEN.search(stripped):
            continue

        if _SECTION_LOCO.match(stripped) and len(stripped) < 90:
            section = "locomotive"
            product = "unknown"
            continue
        if _SECTION_OTHER.match(stripped) and len(stripped) < 90:
            section = "other"
            product = "unknown"
            continue

        if _TITLE_NON_LOCO.match(stripped) and len(stripped) < 100:
            product = "nonloco"
            kind = "Rollendes Material"
            title = stripped[:240]
            continue
        if _TITLE_LOCO.match(stripped) and len(stripped) < 120:
            product = "loco"
            kind = "Lokomotive"
            title = stripped[:240]
            continue

        for m in _SKU_TOKEN.finditer(line):
            if m.group("sound"):
                continue
            art = f"{m.group('a')}{m.group('b')}"
            if art in seen:
                continue
            if not re.fullmatch(r"\d{4,8}", art):
                continue

            accept = False
            if product == "loco" or section == "locomotive":
                accept = True
            elif product == "nonloco" or section == "other":
                accept = False
            elif not locomotives_only:
                accept = True

            if locomotives_only and not accept:
                continue
            if not locomotives_only and product == "nonloco":
                continue

            seen.add(art)
            ctx = (title or stripped)[:240]
            rows.append(
                CatalogRow(
                    article=art,
                    price_eur=None,
                    section=section if section != "none" else "locomotive",
                    kind=kind,
                    line_context=ctx,
                )
            )

    rows.sort(key=lambda r: (r.section, int(r.article), r.kind))
    return rows


def rows_to_queue(
    rows: list[CatalogRow],
    *,
    min_price_eur: Optional[float] = None,
) -> QueueDocument:
    filtered = rows
    if min_price_eur is not None:
        filtered = [
            r
            for r in rows
            if r.price_eur is None or r.price_eur > min_price_eur
        ]
    headers = [
        f"# LS Models catalog extract ({len(filtered)} articles"
        + (f", UVP > {min_price_eur:g} EUR or unknown" if min_price_eur is not None else "")
        + "; prices usually from shop / PDF UVP offen)"
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
