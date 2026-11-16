from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# «39661 Dampflokomotive Baureihe 06» / «30391 Rheingold-Elektrolokomotive …»
_TITLE_LOCO = re.compile(
    r"(?<!\d)(?P<sku>3\d{4})\s+"
    r"(?P<title>(?:\S+-)?(?:Schlepptender-)?(?:Dampf|Diesel|Elektro|Zweikraft)lokomotive)\b"
    r"(?P<rest>.{0,120})",
    re.I,
)
_TITLE_NON_LOCO = re.compile(
    r"(?<!\d)(?P<sku>3\d{4})\s+"
    r"(?P<title>"
    r"Hochgeschwindigkeitszug|Triebwagen|Triebzug|Steuerwagen|"
    r"Personenwagen(?:-Set)?|Güterwagen(?:-Set)?|Ergänzungswagen-Set|"
    r"Niederbordwagen-Set|Doppel-Taschenwagen|Museumswagen-Set|"
    r"Kesselwagen-Set|Schnellzugwagen|Startpackung|Zugpackung"
    r")\b",
    re.I,
)
# Price index rows vary by year:
# «39661  18  699,–» / «36623  41  € 199,95*» / «37008  10  289,99»
_INDEX_ROW = re.compile(
    r"(?<!\d)(?P<sku>3\d{4})\s+(?P<page>U?\d{1,3}(?:,\d{3})?)\s+"
    r"(?:"
    r"€\s*(?P<p_euro>\d{1,3}(?:\.\d{3})*(?:[.,]\d{2})?)\s*\*?"
    r"|"
    r"(?P<p_dash>\d{1,3}(?:\.\d{3})*),\s*[–-]"
    r"|"
    r"(?P<p_cent>\d{1,3}(?:\.\d{3})*[.,]\d{2})\b"
    r")"
)
_INLINE_PRICE = re.compile(
    r"(?:"
    r"€\s*(?P<p_euro>\d{1,3}(?:\.\d{3})*(?:[.,]\d{2})?)\s*\*?"
    r"|"
    r"(?P<p_dash>\d{1,3}(?:\.\d{3})*),\s*[–-]\s*\*?"
    r")"
)


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


def _parse_price(raw: str) -> float:
    t = raw.strip().rstrip("–-*")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d{2}", t):
        # 2.399,99
        return float(t.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d+,\d{2}", t):
        return float(t.replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", t):
        # 2.399 (thousands, no cents)
        return float(t.replace(".", ""))
    if "," in t and "." not in t:
        return float(t.replace(",", "."))
    return float(t.replace(",", ""))


def _kind_from_title(title: str) -> str:
    t = title.strip().lower()
    if "zweikraft" in t:
        return "Zweikraftlok"
    if "dampf" in t:
        return "Dampflok"
    if "diesel" in t:
        return "Diesellok"
    if "elektro" in t:
        return "Elektrolok"
    return "Lokomotive"


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def _price_from_match(m: re.Match[str]) -> Optional[float]:
    raw = m.groupdict().get("p_euro") or m.groupdict().get("p_dash") or m.groupdict().get("p_cent")
    if not raw:
        return None
    try:
        return _parse_price(raw)
    except ValueError:
        return None


def _extract_index_prices(text: str) -> dict[str, float]:
    prices: dict[str, float] = {}
    for m in _INDEX_ROW.finditer(text):
        price = _price_from_match(m)
        if price is not None and price > 0:
            prices[m.group("sku")] = price
    return prices


def extract_maerklin_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract Märklin H0 Neuheiten SKUs from ``pdftotext -layout`` output.

    Prefers the catalog price index (SKU / page / UVP). Product titles classify
    locomotives vs. Wagen/Triebzüge. With ``locomotives_only`` (default), only
    Lokomotiven (inkl. Schlepptender-/Zweikraft) are kept.
    """
    raw = [_norm(line) for line in text.splitlines()]
    prices = _extract_index_prices("\n".join(raw))
    rows: list[CatalogRow] = []
    seen: set[str] = set()
    loco_skus: set[str] = set()
    non_loco_skus: set[str] = set()
    title_meta: dict[str, tuple[str, str]] = {}

    for i, line in enumerate(raw):
        stripped = line.strip()
        if not stripped:
            continue
        non = _TITLE_NON_LOCO.search(stripped)
        if non:
            non_loco_skus.add(non.group("sku"))
            continue
        loco = _TITLE_LOCO.search(stripped)
        if not loco:
            continue
        sku = loco.group("sku")
        kind = _kind_from_title(loco.group("title"))
        rest = loco.group("rest").strip()
        loco_skus.add(sku)
        title_meta.setdefault(sku, (kind, f"{sku} {loco.group('title')} {rest}".strip()[:240]))
        if sku in seen:
            continue
        price = prices.get(sku)
        if price is None:
            for j in range(i, min(len(raw), i + 45)):
                if re.search(r"\(\s*\d+\s*Wagen", raw[j], re.I):
                    continue
                pm = _INLINE_PRICE.search(raw[j])
                if pm:
                    price = _price_from_match(pm)
                    if price is not None:
                        break
        seen.add(sku)
        rows.append(
            CatalogRow(
                article=sku,
                price_eur=price,
                section="locomotive",
                kind=kind,
                line_context=title_meta[sku][1],
            )
        )

    if not locomotives_only:
        for sku, price in sorted(prices.items()):
            if sku in seen or sku in loco_skus:
                continue
            if sku in non_loco_skus:
                kind = "Rollendes Material"
            else:
                kind = "Unbekannt"
            rows.append(
                CatalogRow(
                    article=sku,
                    price_eur=price,
                    section="other",
                    kind=kind,
                    line_context=f"{sku} (price index)",
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
        f"# Maerklin catalog extract ({len(filtered)} articles"
        + (f", UVP > {min_price_eur:g} EUR or unknown" if min_price_eur is not None else "")
        + ")"
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
