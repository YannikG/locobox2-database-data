#!/usr/bin/env python3
"""
Parse PIKO Shop PDP HTML (gespeichert aus Chrome / MCP). Kein HTTP im CLI.

Extrahiert u. a. ``og:title``, ``og:description``, ``og:image``, groben Preis aus
sichtbarem Text, schreibt optional ``articles/piko/{articleNumber}.json``.

Schweizer Textnormalisierung: «ß» → «ss».
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ARTICLES = _REPO_ROOT / "articles" / "piko"


def swiss_text(s: str) -> str:
    return s.replace("\u00df", "ss").replace("ß", "ss")


def _meta_content(html: str, prop: str) -> Optional[str]:
    m = re.search(
        rf'<meta\s+property=["\']{re.escape(prop)}["\']\s+content=["\']([^"\']+)["\']',
        html,
        re.I | re.S,
    )
    if m:
        return html_lib.unescape(m.group(1).strip())
    m2 = re.search(
        rf'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']{re.escape(prop)}["\']',
        html,
        re.I | re.S,
    )
    if m2:
        return html_lib.unescape(m2.group(1).strip())
    return None


def _price_amount(html: str, canonical: str) -> float:
    """Heuristik: erster «…,… €» oder «… €» im sichtbaren Bereich."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    for pat in (
        r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€",
        r"(\d+,\d{2})\s*€",
        r"€\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
    ):
        m = re.search(pat, text)
        if m:
            raw = m.group(1)
            raw = re.sub(r"\.(?=\d{3},)", "", raw).replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                continue
    return 0.0


def _abs_url(base: str, maybe: str) -> str:
    u = (maybe or "").strip()
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith(("http://", "https://")):
        return u
    return urljoin(base.rstrip("/") + "/", u.lstrip("/"))


def parse_html(
    html: str,
    *,
    canonical_url: str,
    article: str,
    image_override: Optional[str],
) -> dict[str, Any]:
    title = _meta_content(html, "og:title") or ""
    if not title.strip():
        m = re.search(r"<title>([^<]+)</title>", html, re.I)
        if m:
            title = html_lib.unescape(m.group(1).strip())
    desc = _meta_content(html, "og:description") or _meta_content(html, "description") or ""
    img = image_override or _meta_content(html, "og:image") or ""
    img = _abs_url(canonical_url, img)
    price = _price_amount(html, canonical_url)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schemaVersion": "1.0.0",
        "id": f"piko-{article}",
        "manufacturer": "PIKO",
        "articleNumber": article,
        "releaseDate": None,
        "uvp": {"amount": price, "currency": "EUR"},
        "model": {
            "country": None,
            "operator": None,
            "type": None,
            "number": None,
            "livery": None,
            "scale": "H0",
            "electricSystem": None,
            "decoderInterface": None,
            "era": None,
            "luepMm": None,
            "minRadiusMm": None,
        },
        "description": swiss_text(desc or title),
        "categories": [],
        "tags": [],
        "source": {
            "url": canonical_url,
            "notes": "Daten von der Webseite, automatisch geupdated.",
            "imageUrl": img or None,
        },
        "updatedAt": now,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="PIKO Shop PDP-HTML → articles/piko JSON.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--html-file", type=Path, help="Gespeichertes PDP-HTML.")
    src.add_argument("--stdin", action="store_true", help="HTML von stdin lesen.")
    ap.add_argument("--canonical-url", required=True, help="Kanonische PDP-URL der Session.")
    ap.add_argument("--article", required=True, help="Artikelnummer (Ziffern).")
    ap.add_argument("--notes", default="Daten von der Webseite, automatisch geupdated.")
    ap.add_argument("--image-url", default=None, help="Bild-URL überschreiben (z. B. aus Netzwerk).")
    ap.add_argument("--write", action="store_true", help="Nach articles/piko/{nr}.json schreiben.")
    ap.add_argument("--quiet", action="store_true", help="Weniger stdout bei --write.")
    args = ap.parse_args()

    if args.stdin:
        html = sys.stdin.read()
    else:
        p = args.html_file.expanduser().resolve()
        if not p.is_file():
            print(f"error: HTML fehlt: {p}", file=sys.stderr)
            return 2
        html = p.read_text(encoding="utf-8", errors="replace")

    data = parse_html(
        html,
        canonical_url=str(args.canonical_url).strip(),
        article=str(args.article).strip(),
        image_override=(str(args.image_url).strip() if args.image_url else None),
    )
    if args.notes:
        data["source"]["notes"] = str(args.notes)

    if args.write:
        out_dir = _DEFAULT_ARTICLES
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{args.article}.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.quiet:
            print(str(out_path))
        return 0

    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
