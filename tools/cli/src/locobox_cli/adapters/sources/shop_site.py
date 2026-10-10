from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ShopSite(Protocol):
    slug: str

    def search_url(self, article: str) -> str: ...

    def is_pdp_url(self, href: str, article: str) -> bool: ...

    def fallback_pdp_url(self, article: str) -> str: ...


@dataclass(frozen=True, slots=True)
class PikoShopSite:
    slug: str = "piko"

    def search_url(self, article: str) -> str:
        return f"https://www.piko-shop.de/de/praesenz/search.html?q={article}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("#")[0].split("?", 1)[0].lower()
        return "piko-shop" in u and "/artikel/" in u and u.endswith(".html") and article in u

    def fallback_pdp_url(self, article: str) -> str:
        return f"https://www.piko-shop.de/de/artikel/{article}.html"


@dataclass(frozen=True, slots=True)
class RocoShopSite:
    slug: str = "roco"

    def search_url(self, article: str) -> str:
        # Magento catalog search (rde = DE shop)
        return f"https://www.roco.cc/rde/catalogsearch/result/?q={article}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("?", 1)[0].lower()
        return "roco.cc" in u and f"/{article}-" in u and u.endswith(".html")

    def fallback_pdp_url(self, article: str) -> str:
        return f"https://www.roco.cc/rde/catalogsearch/result/?q={article}"


def shop_site_for(source: str) -> ShopSite:
    key = source.strip().lower()
    if key == "piko":
        return PikoShopSite()
    if key == "roco":
        return RocoShopSite()
    raise ValueError(f"unknown shop source: {source!r}")
