from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from locobox_cli.domain.article import ArticleNumber


def _compact_sku(article: str) -> str:
    """Shop SKUs omit hyphens (MB263S); Locobox keeps MB-263S."""
    try:
        return ArticleNumber.parse(article).compact().lower()
    except ValueError:
        return article.replace("-", "").replace(" ", "").strip().lower()


@dataclass(frozen=True, slots=True)
class ReeShopSite:
    """PrestaShop search on ree-store.com (fiche produit / fiche technique)."""

    slug: str = "ree"

    def search_url(self, article: str) -> str:
        q = _compact_sku(article).upper()
        return f"https://www.ree-store.com/recherche?controller=search&s={quote(q)}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0].lower()
        if "ree-store.com" not in u or not u.endswith(".html"):
            return False
        if "/recherche" in u:
            return False
        compact = _compact_sku(article)
        if not compact:
            return False
        # …-digital-sound-mb263s-065273….html
        return f"-{compact}-" in u or u.endswith(f"-{compact}.html")

    def fallback_pdp_url(self, article: str) -> str:
        return self.search_url(article)
