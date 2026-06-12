#!/usr/bin/env python3
"""
Extract locomotives, Triebzüge, Triebwagen, and freight/passenger cars from
pdftotext output of the PIKO H0 Neuheiten PDF.

**Nur Pipeline-Stufe 1** (Katalog → Artikelnummern + Metadaten). Stufe 2/3 (MCP + PDP-Parser)
sind dieselbe Idee wie bei Roco; siehe ``utils/shop-import/README.md``.

Default input/output: repository ``.tmp/`` (gitignored scratch; not ``tmp/``).

    pdftotext -layout path/to/piko_2026_h0.pdf .tmp/piko_2026_h0.txt
    python3 utils/piko/catalog-extract/extract_piko_h0_catalog.py \
        --articles-queue-out .tmp/piko_shop_article_numbers.txt

Shop-PDP: ``utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py`` (``--articles``,
``--delay``) plus ``piko_shop_parse_pdp.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

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
    (re.compile(r"GÜTERWAGEN|GĂTERWAGEN|GĂTERWAGEN"), "railcar_freight"),
    (re.compile(r"START[-\s]?SETS", re.I), "start_set"),
]

FANSHOP_HEADER = re.compile(r"FÜR\s+ECHTE\s+PIKO\s+FANS|FĂR\s+ECHTE\s+PIKO\s+FANS", re.I)
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
    r"(?<!\d)"
    r"(?P<sku>[12]\d{4}|[4-9]\d{4})"
    r"\s+"
    r"(?P<price>(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})",
)
SKU_AT = re.compile(r"(?<!\d)(?P<sku>[12]\d{4}|[4-9]\d{4})\b")
PRICE_NEAR_EURO = re.compile(
    r"(?P<price>(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})\s*(?:€|â|EUR|\*)",
    re.I,
)


def iter_sku_price_pairs(line: str) -> list[tuple[str, str]]:
    tight = list(SKU_PRICE_TIGHT.finditer(line))
    if tight:
        return [(m.group("sku"), m.group("price")) for m in tight]
    out: list[tuple[str, str]] = []
    skus = list(SKU_AT.finditer(line))
    for j, sm in enumerate(skus):
        start = sm.start()
        end = skus[j + 1].start() if j + 1 < len(skus) else len(line)
        chunk = line[start:end]
        pm = PRICE_NEAR_EURO.search(chunk)
        if pm:
            out.append((sm.group("sku"), pm.group("price")))
    return out


def line_has_euro_marker(line: str) -> bool:
    return "€" in line or "â" in line or "EUR" in line.upper()


def parse_price_eur(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"\.(?=\d{3},)", "", s)
    s = s.replace(",", ".")
    return s


def classify_row_kind(section: str, context: str) -> str:
    if section == "triebzug":
        return "Triebzug"
    if section == "triebwagen_personen":
        if re.search(r"Diesel\s*trieb|Elektro\s*trieb|Elektotrieb|Schienenbus", context, re.I):
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
        if re.search(r"Güterzug|GĂźterzug", context, re.I) and re.search(
            r"Diesel|Dampf|E-Lok|Elektro", context, re.I
        ):
            return "Zug-Set (Lok + Wagen)"
        return "Lokomotive"
    return "Rollendes Material"


def run_extract(
    text_path: Path,
    out_json: Path,
    out_txt: Path,
    articles_queue_out: Path | None,
) -> int:
    if not text_path.is_file():
        print(f"error: Text fehlt: {text_path}\n  zuerst: pdftotext -layout …/piko_2026_h0.pdf {text_path}", file=sys.stderr)
        return 2
    out_json.parent.mkdir(parents=True, exist_ok=True)
    raw = text_path.read_text(encoding="utf-8", errors="replace").splitlines()
    section = "locomotive"
    in_digital = False
    in_fanshop = False
    rows: list[dict[str, str]] = []
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
                if "PERSONENWAGEN" in stripped or "GÜTER" in stripped.upper() or "GĂTER" in stripped:
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

        if not line_has_euro_marker(line):
            continue

        context = " ".join(
            x.strip()
            for x in (raw[i - 2] if i >= 2 else "", raw[i - 1] if i >= 1 else "", line)
            if x.strip()
        )[-500:]

        for sku, pr in iter_sku_price_pairs(line):
            if sku.startswith("99"):
                continue
            if sku in ("55412", "55401", "55406", "55447", "55270", "55499"):
                continue

            if sku in seen:
                continue
            seen.add(sku)

            kind = classify_row_kind(section, context)
            rows.append(
                {
                    "article": sku,
                    "price_eur": parse_price_eur(pr),
                    "price_raw": pr,
                    "section": section,
                    "kind": kind,
                    "line_context": line.strip()[:240],
                }
            )

    rows.sort(key=lambda r: (r["section"], int(r["article"]), r["kind"]))

    out_json.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines_out = [
        "# PIKO H0 Neuheiten 2026, rollendes Material (heuristisch aus Katalog-Text, pdftotext)",
        f"# Anzahl Artikelnummern: {len(rows)}",
        "",
    ]
    for r in rows:
        lines_out.append(
            f"{r['article']}\t{r['kind']}\t{r['section']}\t{r['price_raw']} EUR\t{r['line_context'][:120]}"
        )
    out_txt.write_text("\n".join(lines_out) + "\n", encoding="utf-8")

    if articles_queue_out is not None:
        articles_queue_out.parent.mkdir(parents=True, exist_ok=True)
        nums = sorted({int(r["article"]) for r in rows}, key=lambda n: n)
        articles_queue_out.write_text(
            "\n".join(str(n) for n in nums) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {len(nums)} lines -> {articles_queue_out} (für Shop-MCP --articles)")

    print(f"wrote {len(rows)} rows -> {out_json}\n{out_txt}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="PIKO H0 Katalog-Text → Artikelnummer-Liste (.tmp/).")
    p.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repository-Root (Default: automatisch).",
    )
    p.add_argument(
        "--text-file",
        type=Path,
        default=None,
        help="pdftotext-Ausgabe (Default: <repo>/.tmp/piko_2026_h0.txt).",
    )
    p.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Default: <repo>/.tmp/piko_2026_h0_rolling_stock.json",
    )
    p.add_argument(
        "--out-txt",
        type=Path,
        default=None,
        help="Default: <repo>/.tmp/piko_2026_h0_rolling_stock_list.txt",
    )
    p.add_argument(
        "--articles-queue-out",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Zusätzlich: eine Artikelnummer pro Zeile (gleiches Format wie --articles bei "
            "utils/roco/shop-pdp-parse/roco_mcp_chrome_search_import.py). "
            "Typisch: <repo>/.tmp/piko_shop_article_numbers.txt"
        ),
    )
    args = p.parse_args()
    root = args.repo_root.resolve()
    tmp = root / ".tmp"
    text = args.text_file or tmp / "piko_2026_h0.txt"
    out_json = args.out_json or tmp / "piko_2026_h0_rolling_stock.json"
    out_txt = args.out_txt or tmp / "piko_2026_h0_rolling_stock_list.txt"
    raise SystemExit(run_extract(text, out_json, out_txt, args.articles_queue_out))


if __name__ == "__main__":
    main()
