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
    r"(?:"
    r"\b(?:Dampf|Diesel|Elektro)?lokomotive\b|"
    r"\b(?:Vectron|Traxx|Taurus)\b|"
    r"\b(?:HLE|BB|CC)\s*\d|"
    r"\b(?:RAe|RABe)\b|"
    r"\bRe\s*\d|"
    r"\bBR\s*\d|"
    r"\bX\s*\d{3,}\b|"
    r"\b(?:Autorail|Triebwagen|Triebzug|Picasso)\b"
    r")",
    re.I,
)
_TITLE_NON_LOCO = re.compile(
    r"(?:"
    r"^\s*(?:(?:\d+-tlg\.\s+)?(?:Set|Wagenset|Zugset)\b)|"
    r"^\s*(?:Personenwagen|Güterwagen|Reisezugwagen|Voiture|Wagon)\b|"
    r"\b(?:Apm|Bpm|Bcmz|WLABmz|OCEM|Tagnpps|Airport\s+EXPRESS|"
    r"Nightjet|M6|I2)\b"
    r")",
    re.I,
)


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


def _is_uic_fragment(line: str, start: int, end: int) -> bool:
    """Reject tokens that are slices of UIC wagon numbers (…59-91 217-4)."""
    before = line[:start].rstrip()
    after = line[end:]
    if before.endswith("-") or before.endswith("–"):
        return True
    if re.match(r"\s*-\d", after):
        return True
    return False


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

        has_sku = bool(_SKU_TOKEN.search(stripped))

        if not has_sku and _TITLE_LOCO.search(stripped) and len(stripped) < 120:
            product = "loco"
            title = stripped[:240]
            continue
        if not has_sku and _TITLE_NON_LOCO.search(stripped) and len(stripped) < 120:
            product = "nonloco"
            title = stripped[:240]
            continue

        # Set lines with SKUs inherit prior loco title (e.g. RAe / HLE).
        if has_sku and re.match(r"^\s*Set\b", stripped, re.I) and product != "loco":
            if section != "locomotive" and not _TITLE_LOCO.search(title):
                product = "nonloco"

        for m in _SKU_TOKEN.finditer(line):
            if m.group("sound"):
                continue
            if _is_uic_fragment(line, m.start(), m.end()):
                continue
            art = f"{m.group('a')}{m.group('b')}"
            if art in seen or not re.fullmatch(r"\d{4,8}", art):
                continue

            # Explicit product wins over a sticky section header (e.g. M6 after HLE).
            is_loco = product == "loco" or (
                section == "locomotive" and product != "nonloco"
            )
            if locomotives_only and not is_loco:
                continue

            out_section = section if section != "none" else ("locomotive" if is_loco else "other")
            out_kind = "Lokomotive" if is_loco else "Rollendes Material"
            seen.add(art)
            rows.append(
                CatalogRow(
                    article=art,
                    price_eur=None,
                    section=out_section,
                    kind=out_kind,
                    line_context=(title or stripped)[:240],
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
