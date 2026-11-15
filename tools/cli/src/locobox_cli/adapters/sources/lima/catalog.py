from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# Lima Expert (HL) / Hobby+accessories (HC). Allow optional space: «HL 2664».
_SKU = re.compile(r"\b(?P<pre>H[LC])\s*(?P<num>\d{3,5})\b", re.I)

_TITLE_LOCO = re.compile(
    r"(?P<title>"
    r"(?:locomotiva\s+(?:elettrica|diesel|a\s+vapore)|"
    r"(?:Elektro|Diesel|Dampf)lokomotive|"
    r"electric\s+locomotive|diesel\s+(?:locomotive|railcar)|steam\s+locomotive|"
    r"automotrice\s+diesel|elettromotrice)"
    r")\b",
    re.I,
)
_TITLE_NON_LOCO = re.compile(
    r"(?P<title>"
    r"(?:set\s+(?:di\s+)?(?:\d+\s+)?(?:carrozze|carri|vagoni)|"
    r"carrozza|carro\b|wagons?|coaches?|"
    r"personenwagen|güterwagen|triebwagen|triebzug|"
    r"elettrotreno|high-?speed\s+emu|"
    r"set\s+base|base\s+pack|add(?:itional|\.)\s+coaches?)"
    r")\b",
    re.I,
)
_INLINE_PRICE = re.compile(
    r"(?:€|EUR|UVP)\s*(?P<price>\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{1,2})?)",
    re.I,
)


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


def _canon_sku(pre: str, num: str) -> str:
    return f"{pre.upper()}{num}"


def _parse_price(raw: str) -> float:
    t = raw.replace(" ", "").replace(".", "").replace(",", ".")
    return float(t)


def _kind_from_title(title: str) -> str:
    t = title.strip().lower()
    if "elettric" in t or "elektro" in t or "electric" in t:
        return "Elektrolok"
    if "diesel" in t or "automotrice" in t:
        return "Diesellok"
    if "vapor" in t or "dampf" in t or "steam" in t:
        return "Dampflok"
    return "Lokomotive"


def _sort_key(article: str) -> tuple[str, int]:
    m = re.fullmatch(r"(H[LC])(\d{3,5})", article, re.I)
    if m:
        return (m.group(1).upper(), int(m.group(2)))
    return (article, 0)


def _block_until_next_sku(lines: list[str], start: int, sku_end_in_line: int) -> str:
    """Text from the SKU match to the next SKU (avoids stealing neighbour prices/titles)."""
    parts: list[str] = []
    first = lines[start]
    # Prefer text after the current SKU on the same line.
    same = first[sku_end_in_line:].strip()
    if same:
        parts.append(same)
    for j in range(start + 1, min(len(lines), start + 12)):
        stripped = lines[j].strip()
        if not stripped:
            continue
        if _SKU.search(stripped):
            break
        parts.append(stripped)
    return " ".join(parts)


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: Optional[float]
    section: str
    kind: str
    line_context: str


def extract_lima_catalog_rows(
    text: str,
    *,
    locomotives_only: bool = True,
) -> list[CatalogRow]:
    """
    Extract Lima Expert / Hobby SKUs from ``pdftotext -layout`` catalog text.

    Recognises ``HL####`` (Expert) and ``HC####`` (Hobby/Zubehör). With
    ``locomotives_only`` (default), Wagen-/Set-/ETR-titles are skipped; bare
    ``HL`` without a title are kept as locomotive candidates, bare ``HC`` not.
    """
    raw = [_norm(line) for line in text.splitlines()]
    rows: list[CatalogRow] = []
    seen: set[str] = set()

    for i, line in enumerate(raw):
        stripped = line.strip()
        if not stripped:
            continue
        for sm in _SKU.finditer(stripped):
            sku = _canon_sku(sm.group("pre"), sm.group("num"))
            if sku in seen:
                continue

            block = _block_until_next_sku(raw, i, sm.end())
            # Same-line prefix before SKU can hold the product family word.
            prefix = stripped[: sm.start()].strip()
            window = f"{prefix} {block}".strip()

            non = _TITLE_NON_LOCO.search(window)
            loco = _TITLE_LOCO.search(window)
            price: Optional[float] = None
            pm = _INLINE_PRICE.search(block) or _INLINE_PRICE.search(stripped)
            if pm:
                try:
                    price = _parse_price(pm.group("price"))
                except ValueError:
                    price = None

            is_loco = bool(loco) and not (
                non is not None and (loco is None or non.start() < loco.start())
            )
            if locomotives_only:
                if non and not loco:
                    continue
                if sku.startswith("HC") and not is_loco:
                    continue
                if not is_loco and not sku.startswith("HL"):
                    continue
                if non and loco and non.start() < loco.start():
                    continue
                kind = _kind_from_title(loco.group("title")) if loco else "Lokomotive"
                section = "locomotive"
            else:
                if is_loco:
                    kind = _kind_from_title(loco.group("title") if loco else "")
                    section = "locomotive"
                elif non:
                    kind = swiss_ss(non.group("title"))[:80]
                    section = "other"
                else:
                    kind = "Hobby" if sku.startswith("HC") else "Unbekannt"
                    section = "other"

            seen.add(sku)
            ctx = (stripped + (" " + block if block else ""))[:240]
            rows.append(
                CatalogRow(
                    article=sku,
                    price_eur=price,
                    section=section,
                    kind=kind,
                    line_context=ctx,
                )
            )

    rows.sort(key=lambda r: (r.section, _sort_key(r.article), r.kind))
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
        f"# Lima catalog extract ({len(filtered)} articles"
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
