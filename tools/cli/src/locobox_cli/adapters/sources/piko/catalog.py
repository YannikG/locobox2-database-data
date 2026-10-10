from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from locobox_cli.domain.queue import QueueDocument, QueueEntry
from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.text import swiss_ss


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s))


HEADER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ELEKTROLOKOMOTIVEN"), "locomotive"),
    (re.compile(r"DIESELLOKOMOTIVEN"), "locomotive"),
    (re.compile(r"DAMPFLOKOMOTIVEN"), "locomotive"),
    (re.compile(r"ZWEIKRAFTLOKOMOTIVEN"), "locomotive"),
    (re.compile(r"(?<!DIESEL)(?<!DAMPF)(?<!ELEKTRO)(?<!ZWEIKRAFT)\bLOKOMOTIVEN\b"), "locomotive"),
    (re.compile(r"PIKO\s+SHOP\s+SYSTEM\s+H"), "locomotive"),
    (re.compile(r"TRIEBWAGEN\s*&\s*PERSONEN"), "triebwagen_personen"),
    (re.compile(r"TRIEBZ"), "triebzug"),
    (re.compile(r"PERSONENWAGEN"), "railcar_passenger"),
    (re.compile(r"GÜTERWAGEN"), "railcar_freight"),
    (re.compile(r"START[-\s]?SETS", re.I), "start_set"),
]

FANSHOP_HEADER = re.compile(r"FÜR\s+ECHTE\s+PIKO\s+FANS", re.I)
DIGITAL_HEADER = re.compile(r"^\s*PIKO\s+DIGITAL\s*$", re.I)
ACCESSORY_LINE = re.compile(
    r"LED-|Decoder|SmartDecoder|SmartProgrammer|Servo\s+Switch|"
    r"Schaltdecoder|RD\s+4000|SD\s+2000|Software\s+Upgrade|"
    r"Stellpult|Wechselstromspeichen|Haftreifen|Radsatz|"
    r"PIKO\s+Servo|PSP-|SmartBooster|SmartControllerwlan|SmartBoxwlan|"
    r"Schnellanleitung|Netzadapter\s*\(|"
    r"G\s+Bahnhof|G\s+Stellwerk|G\s+Fachwerkhaus|Bahnhof\s+Neuffen",
    re.I,
)
SKU_PRICE_TIGHT = re.compile(
    r"(?<!\d)(?P<sku>[12]\d{4}|[4-9]\d{4})\s+(?P<price>(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})"
)
SKU_AT = re.compile(r"(?<!\d)(?P<sku>[12]\d{4}|[4-9]\d{4})\b")
PRICE_NEAR_EURO = re.compile(
    r"(?P<price>(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})\s*(?:€|EUR|\*)",
    re.I,
)
SKIP_SKUS = frozenset({"55412", "55401", "55406", "55447", "55270", "55499"})


@dataclass(frozen=True, slots=True)
class CatalogRow:
    article: str
    price_eur: float
    section: str
    kind: str
    line_context: str


def _iter_sku_price_pairs(line: str) -> list[tuple[str, str]]:
    tight = list(SKU_PRICE_TIGHT.finditer(line))
    if tight:
        return [(m.group("sku"), m.group("price")) for m in tight]
    out: list[tuple[str, str]] = []
    skus = list(SKU_AT.finditer(line))
    for j, sm in enumerate(skus):
        start = sm.start()
        end = skus[j + 1].start() if j + 1 < len(skus) else len(line)
        pm = PRICE_NEAR_EURO.search(line[start:end])
        if pm:
            out.append((sm.group("sku"), pm.group("price")))
    return out


def _parse_price(raw: str) -> float:
    s = re.sub(r"\.(?=\d{3},)", "", raw.strip()).replace(",", ".")
    return float(s)


def _classify(section: str, context: str) -> str:
    if section == "triebzug":
        return "Triebzug"
    if section == "triebwagen_personen":
        if re.search(r"Diesel\s*trieb|Elektro\s*trieb|Schienenbus", context, re.I):
            return "Triebwagen"
        return "Personenwagen"
    if section == "railcar_passenger":
        return "Personenwagen"
    if section == "railcar_freight":
        return "Güterwagen"
    if section == "start_set":
        return "Start-Set"
    if section == "locomotive":
        if re.search(r"Dampflok", context, re.I):
            return "Dampflok"
        if re.search(r"Diesellok", context, re.I):
            return "Diesellok"
        if re.search(r"Elektrolok|E-Lok\b", context, re.I):
            return "Elektrolok"
        if re.search(r"Zweikraft", context, re.I):
            return "Zweikraftlok"
        return "Lokomotive"
    return "Rollendes Material"


def extract_piko_catalog_rows(text: str) -> list[CatalogRow]:
    raw = [_norm(line) for line in text.splitlines()]
    section = "locomotive"
    in_digital = False
    in_fanshop = False
    rows: list[CatalogRow] = []
    seen: set[str] = set()

    for i, line in enumerate(raw):
        stripped = line.strip()
        if not stripped:
            continue
        if DIGITAL_HEADER.match(stripped):
            in_digital = True
            continue
        if FANSHOP_HEADER.search(stripped) and len(stripped) < 80:
            in_fanshop = True
        for pat, name in HEADER_PATTERNS:
            if pat.search(stripped) and len(stripped) < 120:
                section = name
                if name != "locomotive" or "SHOP SYSTEM" in stripped.upper():
                    in_digital = False
                if "PERSONENWAGEN" in stripped or "GÜTER" in stripped.upper():
                    in_fanshop = False
                if "TRIEBWAGEN" in stripped.upper() or "TRIEBZ" in stripped.upper():
                    in_fanshop = False
                    in_digital = False
                break
        if "Komplett" in stripped and "H0" in stripped:
            in_fanshop = False
        if in_digital or in_fanshop:
            continue
        if ACCESSORY_LINE.search(line):
            continue
        if "€" not in line and "EUR" not in line.upper():
            continue
        context = " ".join(
            x.strip()
            for x in (raw[i - 2] if i >= 2 else "", raw[i - 1] if i >= 1 else "", line)
            if x.strip()
        )[-500:]
        for sku, pr in _iter_sku_price_pairs(line):
            if sku.startswith("99") or sku in SKIP_SKUS or sku in seen:
                continue
            seen.add(sku)
            rows.append(
                CatalogRow(
                    article=sku,
                    price_eur=_parse_price(pr),
                    section=section,
                    kind=_classify(section, context),
                    line_context=stripped[:240],
                )
            )
    rows.sort(key=lambda r: (r.section, int(r.article), r.kind))
    return rows


def rows_to_queue(rows: list[CatalogRow], *, min_price_eur: Optional[float] = None) -> QueueDocument:
    filtered = rows
    if min_price_eur is not None:
        filtered = [r for r in rows if r.price_eur > min_price_eur]
    headers = [
        f"# PIKO catalog extract ({len(filtered)} articles"
        + (f", UVP > {min_price_eur:g} EUR" if min_price_eur is not None else "")
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
