from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

from locobox_cli.domain.text import swiss_ss

_SKU_LINE = re.compile(r"(?<![A-Za-z0-9])HJ(?P<digits>\d{4})(?P<sound>S)?(?![A-Za-z0-9])", re.I)
_DE_TITLE = re.compile(
    r"^SNCF,\s*(?P<title>.+?)$",
    re.I,
)
_ERA = re.compile(r"\b([IVX]{1,4})\b")
_NUMBERISH = re.compile(
    r"\b("
    r"\d{1,2}-\d{3}\s*[A-Z]\s*\d+"  # 2-040 D 65
    r"|"
    r"\d{3}\s*P\s*\d+"  # 241 P 16
    r"|"
    r"BB\s*\d+"
    r"|"
    r"CC\s*\d+"
    r"|"
    r"X\s*\d+"
    r"|"
    r"\d{5,6}"
    r")\b",
    re.I,
)


def _norm(s: str) -> str:
    return swiss_ss(unicodedata.normalize("NFC", s)).strip()


def _categories_for_kind(kind: str) -> list[str]:
    cats = ["lokomotive"]
    k = kind.lower()
    if "dampf" in k:
        cats.append("dampflokomotive")
    elif "diesel" in k:
        cats.append("diesellokomotive")
    elif "elektro" in k:
        cats.append("elektrolokomotive")
    if "triebwagen" in k or "autorail" in k or "railcar" in k:
        cats = ["triebwagen", "dieseltriebwagen" if "diesel" in k else "triebwagen"]
    return cats


def _guess_type_and_number(de_title: str) -> tuple[str, Optional[str]]:
    t = de_title
    # Strip leading class words for type seed
    type_seed = re.sub(
        r"^(Dampflokomotive|Diesellokomotive|Mehrsystemelektrolokomotive|"
        r"Elektrolokomotive|Dieseltriebwagen|Autorail|locomotive[^,]*)\s+",
        "",
        t,
        flags=re.I,
    ).strip()
    type_seed = type_seed.split(",")[0].strip()
    type_seed = re.sub(r"\s+mit\s+Tender.*$", "", type_seed, flags=re.I).strip()
    type_seed = re.sub(r"\s+in\s+.*Farbgebung.*$", "", type_seed, flags=re.I).strip()
    type_seed = re.sub(r"\s+[„\"].*$", "", type_seed).strip()
    if not type_seed:
        type_seed = t[:80]
    num = None
    m = _NUMBERISH.search(t)
    if m:
        num = re.sub(r"\s+", " ", m.group(1)).strip()
    return type_seed[:120], num


def _guess_livery(de_title: str) -> Optional[str]:
    m = re.search(r"[„\"](.+?)[”“\"]", de_title)
    if m:
        return m.group(1).strip()
    m = re.search(r"Farbgebung\s+[„\"]?(.+?)[”“\"]?\s*$", de_title, re.I)
    if m:
        return m.group(1).strip(" ,.")
    m = re.search(r"livrée\s+[«\"](.+?)[»\"]", de_title, re.I)
    if m:
        return m.group(1).strip()
    return None


def _guess_era(block: str) -> str:
    # Prefer standalone era tokens near the SKU (roman numerals).
    for m in _ERA.finditer(block):
        val = m.group(1)
        if val in {"I", "II", "III", "IV", "V", "VI"}:
            return val
    return "Unbekannt"


def index_catalog_blocks(text: str) -> dict[str, dict[str, str]]:
    """Map HJ#### / HJ####S → German title + raw block snippet."""
    lines = [_norm(l) for l in text.splitlines()]
    out: dict[str, dict[str, str]] = {}
    for i, line in enumerate(lines):
        if not _SKU_LINE.search(line):
            continue
        skus = []
        for m in _SKU_LINE.finditer(line):
            digits = m.group("digits")
            sound = (m.group("sound") or "").upper()
            skus.append(f"HJ{digits}{sound}")
        window = lines[i : min(len(lines), i + 18)]
        de_title = ""
        fr_title = ""
        for w in window[1:]:
            if w.startswith("SNCF,") and ("lok" in w.lower() or "trieb" in w.lower() or "Dampflok" in w or "Diesel" in w or "Elektro" in w or "autorail" in w.lower()):
                if "Dampflokomotive" in w or "Diesellokomotive" in w or "Elektrolokomotive" in w or "Dieseltriebwagen" in w or "Mehrsystem" in w:
                    de_title = w
                    break
                if not fr_title and ("locomotive" in w.lower() or "autorail" in w.lower()):
                    fr_title = w
            if w.startswith("SNCF,") and ("Dampflokomotive" in w or "Diesellokomotive" in w or "Elektrolokomotive" in w or "Dieseltriebwagen" in w or "Mehrsystemelektrolokomotive" in w):
                de_title = w
                break
        if not de_title:
            for w in window[1:]:
                if w.startswith("SNCF,"):
                    # Prefer German-looking lines
                    if any(x in w for x in ("lokomotive", "Lokomotive", "Triebwagen", "Farbgebung")):
                        de_title = w
                        break
                    if not fr_title:
                        fr_title = w
        title = de_title or fr_title
        block = "\n".join(window)
        for sku in skus:
            out.setdefault(
                sku,
                {
                    "title": title[5:].strip() if title.lower().startswith("sncf,") else title,
                    "raw_title": title,
                    "block": block,
                },
            )
    return out


def build_jouef_article(
    *,
    article: str,
    kind: str,
    year: int,
    tag: str,
    catalog_meta: Optional[dict[str, str]] = None,
    source_url: str = "https://fr.jouef.com/catalogue",
) -> dict[str, Any]:
    meta = catalog_meta or {}
    de_title = meta.get("title") or article
    model_type, number = _guess_type_and_number(de_title)
    livery = _guess_livery(de_title)
    era = _guess_era(meta.get("block") or "")
    sound = article.endswith("S")
    electric = "DC-Digital" if sound else "DC-Analog"
    features = ["sound"] if sound else []
    desc = _norm(de_title) if de_title else article
    if sound and "Sound" not in desc:
        desc = f"{desc} (Werkseitig mit Sound)."
    cats = _categories_for_kind(kind)
    # Triebwagen override from title
    if re.search(r"autorail|triebwagen|railcar|RGP|X\s*73500", de_title, re.I):
        cats = ["triebwagen"]
        if re.search(r"diesel|autorail|RGP|X\s*73500", de_title, re.I):
            cats.append("dieseltriebwagen")
        kind_label = "Dieseltriebwagen"
    else:
        kind_label = kind

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    art: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "id": f"jouef-{article}",
        "manufacturer": "Jouef",
        "articleNumber": article,
        "releaseDate": str(year),
        "uvp": None,
        "model": {
            "country": "FR",
            "operator": "SNCF",
            "type": model_type or kind_label,
            "number": number,
            "livery": livery,
            "scale": "H0",
            "electricSystem": electric,
            # Hornby/Jouef H0 motorized line: Digitalschnittstelle NEM 660 (21-pin MTC).
            "decoderInterface": "NEM 660 (21MTC)",
            "era": era,
            "luepMm": None,
            "minRadiusMm": None,
        },
        "description": desc,
        "categories": cats,
        "tags": [tag],
        "source": {
            "url": source_url,
            "notes": "Catalog-only Import (offizieller Shop ohne stabile PDP); Daten aus Jouef/Hornby-Katalogtext.",
        },
        "updatedAt": now,
    }
    if features:
        art["model"]["features"] = features
    if article.endswith("S"):
        art["model"]["variantGroup"] = article[:-1]
    elif not article.endswith("S"):
        art["model"]["variantGroup"] = article
    return art
