from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# Flyer / catalog titles (IT / DE / EN). Short header lines only.
_LOCO_HEADER = re.compile(
    r"^\s*(?:"
    r"Locomotiva(?:\s+(?:elettrica|diesel|a\s+vapore))?\b|"
    r"(?:Dampf|Diesel|Elektro)?lokomotiven?\b|"
    r"(?:Electric|Diesel|Steam)\s+locomotives?\b"
    r")",
    re.I,
)
_LOCO_BODY = re.compile(
    r"^\s*(?:"
    r"Locomotiva\b|"
    r"Lokomotive\b|"
    r"(?:Electric|Diesel|Steam)\s+locomotive\b"
    r")",
    re.I,
)
_NON_LOCO_TITLE = re.compile(
    r"^\s*(?:"
    r"Set\s+di\b|"
    r"Carrozza\b|"
    r"(?:\d+-tlg\.\s+)?(?:Wagenset|Zugset|Startset)\b|"
    r"Personenwagen\b|Güterwagen\b|Reisezugwagen\b|"
    r"Treno\s+(?:ad\s+alta|Pop|notturno|navetta)\b|"
    r"Hochgeschwindigkeitszug\b|"
    r"Passenger\s+coaches?\b|Goods\s+wagons?\b"
    r")",
    re.I,
)
# Main article: optional AC prefix, five digits (e.g. AC60655 / 60655).
_SKU = re.compile(r"(?<![A-Za-z0-9])(?:AC)?(?P<sku>\d{5})(?!\d)", re.I)
# Flyer layout: «60655                        212» (SKU + UVP EUR, no currency sign).
_SKU_PRICE = re.compile(
    r"(?<![A-Za-z0-9])(?:AC)?(?P<sku>\d{5})(?!\d)\s+(?P<price>\d{2,4})\b",
    re.I,
)
# Sound / AC-sound siblings often 69xxx next to 60xxx DC locos.
_LOCO_PREFIXES = ("60", "69")
_NON_LOCO_PREFIXES = ("50", "51", "52", "55", "70", "79", "90")
# Herbst layout: UVP alone on the next line under a pair of loco SKUs.
_ORPHAN_PRICE = re.compile(r"^\s*(?P<price>\d{2,4})\s*$")


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


def _kind_from_title(title: str) -> str:
    t = title.strip().lower()
    if "vapore" in t or "dampf" in t or "steam" in t:
        return "Dampflok"
    if "diesel" in t:
        return "Diesellok"
    if "elettric" in t or "elektro" in t or "electric" in t:
        return "Elektrolok"
    return "Lokomotive"


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def extract_acme_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract ACME catalog / flyer SKUs from ``pdftotext -layout`` output.

    ACME has no webshop; product sheets are flyer PDFs
    (``https://www.acmetreni.it/files/AC{article}.pdf``) and year catalogs.
    Article numbers are five digits (often printed as ``AC60655``); sound
    variants commonly use ``69xxx`` beside DC ``60xxx``.

    Catalog pages usually omit a currency mark; ``price_eur`` is taken from a
    SKU+number pair when present. With ``locomotives_only`` (default), wagon
    sets / carrozze / high-speed sets are skipped.
    """
    raw = [_norm(line) for line in text.splitlines()]
    product = "unknown"  # loco | nonloco | unknown
    kind = "Lokomotive"
    title = ""
    rows: list[CatalogRow] = []
    seen: set[str] = set()
    prices: dict[str, float] = {}
    pending_price_skus: list[str] = []

    for line in raw:
        stripped = line.strip()
        if not stripped:
            continue

        orphan = _ORPHAN_PRICE.match(stripped)
        if orphan and pending_price_skus:
            price = float(orphan.group("price"))
            for sku in pending_price_skus:
                prices.setdefault(sku, price)
            pending_price_skus = []
            continue

        if _NON_LOCO_TITLE.match(stripped) and len(stripped) < 120:
            product = "nonloco"
            kind = stripped.split()[0][:40]
            title = stripped[:240]
            pending_price_skus = []
            continue

        loco = _LOCO_HEADER.match(stripped) or _LOCO_BODY.match(stripped)
        if loco and len(stripped) < 160:
            product = "loco"
            kind = _kind_from_title(stripped)
            title = stripped[:240]
            continue

        line_skus: list[str] = []
        for m in _SKU_PRICE.finditer(line):
            prices[m.group("sku")] = float(m.group("price"))

        for m in _SKU.finditer(line):
            art = m.group("sku")
            if art in seen:
                continue
            if art.startswith(_NON_LOCO_PREFIXES) and product != "loco":
                # Hard non-loco families unless a loco title just claimed the page.
                if locomotives_only or product == "nonloco":
                    continue
            if art.startswith(_NON_LOCO_PREFIXES) and product == "loco":
                # Exclusive codes (90xxx) / set SKUs on a loco flyer are not the loco.
                if art.startswith(("90", "70", "79", "55", "50", "51", "52")):
                    continue

            accept = False
            row_kind = kind if product == "loco" else "Lokomotive"
            # 60xxx / 69xxx are always locomotives in ACME numbering, even when
            # the previous block was a set/coach page (Herbst: SKU before title).
            if art.startswith(_LOCO_PREFIXES):
                accept = True
                if product == "loco":
                    row_kind = kind
            elif product == "loco":
                accept = True
            elif product == "nonloco":
                accept = False

            if locomotives_only and not accept:
                continue
            if not locomotives_only:
                if not accept:
                    if product != "loco" or art.startswith(_NON_LOCO_PREFIXES):
                        continue
                    accept = True

            seen.add(art)
            line_skus.append(art)
            ctx = (title or stripped)[:240]
            rows.append(
                CatalogRow(
                    article=art,
                    price_eur=prices.get(art),
                    section="locomotive" if accept else "other",
                    kind=row_kind if accept else (kind if product != "unknown" else "Unbekannt"),
                    line_context=ctx,
                )
            )

        if line_skus and any(s.startswith(_LOCO_PREFIXES) for s in line_skus):
            pending_price_skus = [s for s in line_skus if s.startswith(_LOCO_PREFIXES)]
        elif not orphan:
            pending_price_skus = []

    # Fill prices discovered after the SKU line (flyer sound SKU then price elsewhere).
    for i, row in enumerate(rows):
        if row.price_eur is None and row.article in prices:
            rows[i] = CatalogRow(
                article=row.article,
                price_eur=prices[row.article],
                section=row.section,
                kind=row.kind,
                line_context=row.line_context,
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
        (
            f"# ACME catalog extract ({len(filtered)} articles"
            + (
                f", UVP > {min_price_eur:g} EUR or unknown"
                if min_price_eur is not None
                else ""
            )
            + "; flyer URL https://www.acmetreni.it/files/AC{article}.pdf)"
        )
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
