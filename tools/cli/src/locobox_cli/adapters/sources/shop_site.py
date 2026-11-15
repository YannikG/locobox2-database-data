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
        u = href.split("#", 1)[0].split("?", 1)[0].lower()
        return "roco.cc" in u and f"/{article}-" in u and u.endswith(".html")

    def fallback_pdp_url(self, article: str) -> str:
        return f"https://www.roco.cc/rde/catalogsearch/result/?q={article}"


@dataclass(frozen=True, slots=True)
class MaerklinShopSite:
    """Shared Shopware shop for Trix, Märklin and LGB (maerklinshop.de)."""

    slug: str = "trix"

    def search_url(self, article: str) -> str:
        # Shopware classic: form field name is sSearch (Artikelnr. ohne Markenpräfix).
        return f"https://www.maerklinshop.de/search?sSearch={article}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0].lower()
        # PDP URLs use internal sArticle ids; article number is only in page content.
        return "maerklinshop.de" in u and "/detail/index/sarticle/" in u

    def fallback_pdp_url(self, article: str) -> str:
        return self.search_url(article)


def shop_site_for(source: str) -> ShopSite:
    from locobox_cli.adapters.sources.lima.shop_site import LimaModelSite
    from locobox_cli.adapters.sources.trix.shop_site import TrixProductDbSite

    key = source.strip().lower()
    if key == "piko":
        return PikoShopSite()
    if key == "roco":
        return RocoShopSite()
    if key == "trix":
        return TrixProductDbSite()
    if key == "lima":
        return LimaModelSite()
    if key in {"maerklin", "marklin", "lgb"}:
        return MaerklinShopSite(slug=key.replace("marklin", "maerklin"))
    raise ValueError(f"unknown shop source: {source!r}")
