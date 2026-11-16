from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# Neuheiten layout: ``1258 168`` / twin ``1358 168`` (4+3 digits).
# Skip slash twins like ``1258/1358 178`` (replacement references).
_SKU_TOKEN = re.compile(r"(?<![/\d])(?P<a>\d{4})\s+(?P<b>\d{3})(?![\d])")

_PRICE = re.compile(
    r"(?P<price>(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})\s*(?:€|EUR|Euro)?",
    re.I,
)

_TITLE_LOCO = re.compile(
    r"(?:"
    r"\bElektrolok(?:omotive)?\b|"
    r"\bDiesellok(?:omotive)?\b|"
    r"\bDampflok(?:omotive)?(?:fertigmodell)?\b|"
    r"\bZahnradlok(?:omotive)?\b|"
    r"\bRangier(?:lok|lokomotive|traktor)\b|"
    r"\bUniversallok(?:omotive)?\b|"
    r"\bDrehgestelle?llok\b|"
    r"\bTriebwagen\b|"
    r"\bTriebzug\b|"
    r"\bLokomotive\b|"
    r"\b(?:H?Ge|Gmf|Gem|Te|Tm)\s*\d|"
    r"\b(?:VL|D)\s*\d{1,3}\b"
    r")",
    re.I,
)
_TITLE_WAGON = re.compile(
    r"(?:"
    r"\bGüterwagen\b|"
    r"\bPersonenwagen\b|"
    r"\bReisezugwagen\b|"
    r"\bPanoramawagen\b|"
    r"\bSpeisewagen\b|"
    r"\bSaalwagen\b|"
    r"\bSchiebewandwagen\b|"
    r"\bKnickkesselwagen\b|"
    r"\bKesselwagen\b|"
    r"\bContainerwagen\b|"
    r"\bBeiwagen\b|"
    r"\bWagenset\b|"
    r"\bEW\s*[IVX]+\b|"
    r"\b(?:Api|Ap|Bp|WRp|WR-?S|WR|Za|Uah|Lb-v|Sb-v|Hai)\b"
    r")",
    re.I,
)

# BEMO family prefixes: motorized vs wagons (7-digit canonical).
_LOCO_PREFIX = re.compile(r"^(?:10|11|12|13|92|93|99)")
_WAGON_PREFIX = re.compile(r"^(?:22|32|95)")


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


def _parse_price(raw: str) -> float:
    s = re.sub(r"\.(?=\d{3},)", "", raw.strip()).replace(",", ".")
    return float(s)


def _kind_from_title(title: str) -> str:
    ctx = title.lower()
    if _TITLE_WAGON.search(title) and not _TITLE_LOCO.search(title):
        if re.search(r"personen|panorama|speise|saal|ew\s", ctx):
            return "Personenwagen"
        return "Güterwagen"
    if re.search(r"triebwagen|triebzug", ctx):
        return "Triebwagen"
    if re.search(r"zahnrad|hge\s*\d", ctx):
        return "Zahnradlok"
    if re.search(r"rangier", ctx):
        return "Rangierlok"
    if re.search(r"dampf", ctx):
        return "Dampflok"
    if re.search(r"diesel|\bvl\s*\d|\bzillertal|\bstlb\b", ctx):
        return "Diesellok"
    if re.search(r"elektro|\bge\s*\d|\buniversallok", ctx):
        return "Elektrolok"
    if _TITLE_LOCO.search(title):
        return "Lokomotive"
    return "Rollendes Material"


def _line_is_wagon(line: str, article: str) -> bool:
    if _TITLE_LOCO.search(line):
        return False
    if _WAGON_PREFIX.match(article):
        return True
    if _TITLE_WAGON.search(line):
        return True
    return False


def _line_is_loco(line: str, article: str, *, product: str) -> bool:
    if _line_is_wagon(line, article):
        return False
    if _TITLE_LOCO.search(line):
        return True
    # Known motorized article families when line is not clearly a wagon.
    if _LOCO_PREFIX.match(article):
        return True
    return product == "loco"


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def extract_bemo_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract BEMO Neuheiten SKUs from ``pdftotext -layout`` output.

    Canonical numbers strip spaces (``1258 168`` → ``1258168``). UVP is often
    absent in flyer PDFs; ``price_eur`` may be ``None``.

    With ``locomotives_only`` (default), keep Elektrolok/Diesellok/Dampflok/
    Triebwagen/Zahnradlok/Rangier*/Metal Collection motorized; skip pure
    Güterwagen/Personenwagen unless ``--all-rolling-stock``.
    """
    raw = [_norm(line) for line in text.splitlines()]
    product = "unknown"  # loco | wagon | unknown
    title = ""
    rows: list[CatalogRow] = []
    seen: set[str] = set()

    for line in raw:
        stripped = line.strip()
        if not stripped:
            continue

        has_sku = bool(_SKU_TOKEN.search(stripped))
        if not has_sku and _TITLE_LOCO.search(stripped) and len(stripped) < 160:
            product = "loco"
            title = stripped[:240]
            continue
        if not has_sku and _TITLE_WAGON.search(stripped) and len(stripped) < 160:
            product = "wagon"
            title = stripped[:240]
            continue

        if not has_sku:
            continue

        price: Optional[float] = None
        pm = _PRICE.search(stripped)
        if pm:
            try:
                price = _parse_price(pm.group("price"))
            except ValueError:
                price = None

        for m in _SKU_TOKEN.finditer(stripped):
            art = f"{m.group('a')}{m.group('b')}"
            if art in seen:
                continue
            try:
                ArticleNumber.parse(art)
            except ValueError:
                continue

            ctx = f"{title} {stripped}".strip()
            is_loco = _line_is_loco(ctx, art, product=product)
            if locomotives_only and not is_loco:
                continue

            seen.add(art)
            kind = _kind_from_title(ctx)
            section = "locomotive" if is_loco else "rolling"
            rows.append(
                CatalogRow(
                    article=art,
                    price_eur=price,
                    section=section,
                    kind=kind,
                    line_context=ctx[:240],
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
        f"# BEMO catalog extract ({len(filtered)} articles"
        + (
            f", UVP > {min_price_eur:g} EUR or unknown"
            if min_price_eur is not None
            else ""
        )
        + "; motorized / locomotives preferred)"
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
