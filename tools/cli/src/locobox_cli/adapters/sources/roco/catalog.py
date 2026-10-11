from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# TT/H0 Neuheiten catalogs: product title then SKU + DC/DCC (prices live in the shop).
_SECTION_LOCO = re.compile(
    r"^\s*(Dampflokomotiven|Elektrolokomotiven|Diesellokomotiven)\b",
    re.I,
)
_SECTION_OTHER = re.compile(
    r"^\s*(Personenwagen|Güterwagen|Startsets|COLLECTOR'?S?\s*EDITION|"
    r"Was finde ich wo|Impressum|Reisezugwagen|Beiwagen|Railjet)\b",
    re.I,
)
_TITLE_LOCO = re.compile(
    r"^\s*((?:Dampf|Diesel|Elektro)lokomotive)\b(.{0,120})$",
    re.I,
)
_TITLE_NON_LOCO = re.compile(
    r"^\s*(Dieseltriebwagen|Elektrotriebwagen|Triebwagen|Beiwagen|"
    r"Reisezugwagen|Güterwagen|Startset|Taschenwagen|Packwagen)\b",
    re.I,
)
_SKU_DC = re.compile(r"(?<!\d)(\d{7})\s+(DC|DCC)\b")
# Wagon / set / trailer families that appear next to loco pages in TT catalogs.
_NON_LOCO_PREFIXES = ("628", "629", "408", "348", "669", "778", "779")
_LOCO_PREFIXES = ("718", "719", "738", "739", "758", "759")


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def _kind_from_title(title_kind: str) -> str:
    t = title_kind.strip().lower()
    if t.startswith("dampf"):
        return "Dampflok"
    if t.startswith("diesel"):
        return "Diesellok"
    if t.startswith("elektro"):
        return "Elektrolok"
    return "Lokomotive"


def extract_roco_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract Roco Neuheiten catalog SKUs from ``pdftotext -layout`` output.

    Catalog PDFs typically omit UVP; ``price_eur`` is therefore ``None``.
    With ``locomotives_only`` (default), Triebwagen/Wagen/Startsets are skipped.
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

        if _SECTION_LOCO.match(stripped) and len(stripped) < 60:
            section = "locomotive"
            continue
        if _SECTION_OTHER.match(stripped) and len(stripped) < 80:
            if re.match(r"COLLECTOR", stripped, re.I):
                section = "collector"
            elif re.match(r"Railjet", stripped, re.I):
                # Railjet pages mix loco + coaches; rely on product titles.
                section = "railjet"
            else:
                section = "other"
            continue

        non = _TITLE_NON_LOCO.match(stripped)
        if non:
            product = "nonloco"
            kind = non.group(1)
            title = stripped
            continue
        loco = _TITLE_LOCO.match(stripped)
        if loco:
            product = "loco"
            kind = _kind_from_title(loco.group(1))
            title = stripped
            continue

        for sm in _SKU_DC.finditer(line):
            art = sm.group(1)
            if art in seen:
                continue
            if art.startswith(_NON_LOCO_PREFIXES):
                continue

            accept = False
            row_kind = kind
            if product == "loco":
                accept = True
            elif product == "nonloco":
                accept = False
            elif section == "locomotive" and art.startswith(_LOCO_PREFIXES):
                accept = True
                row_kind = row_kind if row_kind != "Lokomotive" else "Lokomotive"
            elif section == "collector" and art.startswith(_LOCO_PREFIXES):
                # Collector edition locos without a fresh title line.
                accept = True
                row_kind = "Diesellok" if art.startswith(("738", "739")) else row_kind
            elif section == "railjet" and art.startswith(("758", "759")):
                accept = True
                row_kind = "Elektrolok"

            if locomotives_only and not accept:
                continue
            if not locomotives_only and product == "nonloco":
                continue
            if not accept and not locomotives_only:
                # Broad extract still skips hard non-loco prefixes above.
                if not art.startswith(_LOCO_PREFIXES) and product != "loco":
                    continue

            seen.add(art)
            ctx = (title or stripped)[:240]
            rows.append(
                CatalogRow(
                    article=art,
                    price_eur=None,
                    section=section if section != "none" else "locomotive",
                    kind=row_kind,
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
        # Roco catalog text usually has no prices; keep rows with unknown price
        # and drop only those known to be at or below the threshold.
        filtered = [
            r
            for r in rows
            if r.price_eur is None or r.price_eur > min_price_eur
        ]
    headers = [
        f"# Roco catalog extract ({len(filtered)} articles"
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
