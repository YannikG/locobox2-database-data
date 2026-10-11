from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.text import swiss_ss

# TT/H0 Neuheiten catalogs: product title then SKU + DC/DCC, or older «Art. Nr.:».
# Section headers only (not prose like «Diesellokomotiven der Baureihe …»).
_SECTION_LOCO = re.compile(
    r"^\s*(?:H0\s+)?"
    r"(Dampflokomotiven|Elektrolokomotiven|Diesellokomotiven|"
    r"Dampf-\s*&\s*Elektrolokomotiven)"
    r"(?:\s*/\s*.{0,80})?\s*$",
    re.I,
)
_SECTION_OTHER = re.compile(
    r"^\s*(?:H0\s+)?"
    r"(Personenwagen|Güterwagen|Startsets|COLLECTOR'?S?\s*EDITION|"
    r"Was finde ich wo|Impressum|Reisezugwagen|Beiwagen|Railjet|"
    r"Passenger coaches|Goods wagons)"
    r"(?:\s*/\s*.{0,80})?\s*$",
    re.I,
)
_TITLE_LOCO = re.compile(
    # Do not require end-of-line: bilingual catalogs often continue with prose.
    r"^\s*((?:Dampf|Diesel|Elektro)lokomotive)\b(.{0,100})",
    re.I,
)
_TITLE_NON_LOCO = re.compile(
    r"^\s*(?:"
    r"(?:\d+-tlg\.\s+)?(?P<set>Set|Wagenset|Zugset)\b|"
    r"(?P<other>Dieseltriebwagen|Elektrotriebwagen|Dieseltriebzug|Elektrotriebzug|"
    r"Triebwagen|Beiwagen|Reisezugwagen|Personenwagen|Güterwagen|"
    r"Startset|Taschenwagen|Packwagen|Zwischenwagen|Doppelstockwagen|"
    r"Schlafwagen|Silowagen)\b"
    r")",
    re.I,
)
_SKU_DC = re.compile(r"(?<!\d)(\d{7})\s+(DC|DCC)\b")
# Older H0 catalogs (e.g. Winterneuheiten 2018/19): «Art. Nr.: 72016»
_SKU_ART_NR = re.compile(r"Art\.\s*Nr\.:\s*(\d{5,7})\b", re.I)
# H0e year catalogs: SKU + decoder count «33298  4/1» or «33253  3/0»
_SKU_DECODER_FRAC = re.compile(r"(?<!\d)(\d{5,7})\s+(\d/\d)\b")
# Wagon / set / trailer families that appear next to loco pages in TT catalogs.
_NON_LOCO_PREFIXES = ("628", "629", "408", "348", "669", "778", "779", "614", "641", "664", "671")
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

        if _SECTION_LOCO.match(stripped) and len(stripped) < 90:
            section = "locomotive"
            product = "unknown"
            continue
        if _SECTION_OTHER.match(stripped) and len(stripped) < 90:
            if re.match(r"COLLECTOR", stripped, re.I):
                section = "collector"
            elif re.match(r"Railjet", stripped, re.I):
                # Railjet pages mix loco + coaches; rely on product titles.
                section = "railjet"
            else:
                section = "other"
            product = "unknown"
            continue

        non = _TITLE_NON_LOCO.match(stripped)
        if non:
            is_set = bool(non.group("set"))
            # Product titles are short and usually «Gattung, Operator»;
            # wrapped prose like «Doppelstockwagen von …» must not win.
            if is_set or (len(stripped) < 90 and "," in stripped):
                product = "nonloco"
                kind = (non.group("set") or non.group("other") or "Set").strip()
                title = stripped[:240]
                continue
        loco = _TITLE_LOCO.match(stripped)
        if loco:
            product = "loco"
            kind = _kind_from_title(loco.group(1))
            # Keep short title only (drop bilingual prose on same line).
            title = f"{loco.group(1)}{loco.group(2)}".strip()
            title = re.split(r"\s{2,}", title, maxsplit=1)[0].strip()[:240]
            continue

        sku_hits: list[str] = [m.group(1) for m in _SKU_DC.finditer(line)]
        sku_hits.extend(m.group(1) for m in _SKU_ART_NR.finditer(line))
        sku_hits.extend(m.group(1) for m in _SKU_DECODER_FRAC.finditer(line))
        # Deduplicate while preserving order (dual SKUs on one H0e page).
        sku_hits = list(dict.fromkeys(sku_hits))
        for art in sku_hits:
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
