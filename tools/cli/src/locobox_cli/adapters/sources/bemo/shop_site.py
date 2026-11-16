from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote_plus


def compact_sku(article: str) -> str:
    """Canonical digits-only SKU (``2295 561`` → ``2295561``)."""
    return re.sub(r"\D", "", article.strip())


def spaced_sku(article: str) -> str:
    """
    Shop search form: 7-digit SKUs as ``1258 168`` (4+3).

    Compact search is noisy on bemo-modellbahn.de; spaced query matches better.
    """
    digits = compact_sku(article)
    if len(digits) == 7:
        return f"{digits[:4]} {digits[4:]}"
    if len(digits) == 8:
        return f"{digits[:4]} {digits[4:]}"
    if len(digits) == 6:
        return f"{digits[:3]} {digits[3:]}"
    return digits


@dataclass(frozen=True, slots=True)
class BemoShopSite:
    """WordPress custom theme shop on bemo-modellbahn.de (not Magento/PrestaShop)."""

    slug: str = "bemo"

    def search_url(self, article: str) -> str:
        q = spaced_sku(article)
        return f"https://www.bemo-modellbahn.de/?s={quote_plus(q)}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        del article  # PDP path is a product slug; SKU lives in page content.
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0]
        parts = u.split("/", 3)
        if len(parts) < 4:
            return False
        host = parts[2].lower()
        if "bemo-modellbahn.de" not in host:
            return False
        path = "/" + parts[3]
        return path.startswith("/produkt/")

    def fallback_pdp_url(self, article: str) -> str:
        return self.search_url(article)
