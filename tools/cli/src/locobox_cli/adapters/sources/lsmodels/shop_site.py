from __future__ import annotations

import re
from dataclasses import dataclass

# PrestaShop pretty URL: /{lang}/{category-slug}/{id}-{product-slug}.html
# Internal product id is not the article number (search → PDP required).
_PDP_PATH = re.compile(
    r"^/[a-z]{2}/[a-z0-9-]+/\d+-[a-z0-9-]+\.html$",
    re.I,
)


@dataclass(frozen=True, slots=True)
class LsModelsShopSite:
    """PrestaShop catalog shop on lsmodels.eu (same catalog as lsmodels.com)."""

    slug: str = "lsmodels"

    def search_url(self, article: str) -> str:
        art = article.strip().replace(" ", "")
        return f"https://lsmodels.eu/de/suche?controller=search&s={art}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        del article  # PDP path uses internal PrestaShop id, not the SKU.
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0]
        host = u.split("/", 3)
        if len(host) < 4:
            return False
        if "lsmodels.eu" not in host[2].lower() and "lsmodels.com" not in host[2].lower():
            return False
        path = "/" + host[3] if len(host) > 3 else ""
        # Drop language-only or category listing paths.
        return bool(_PDP_PATH.match(path))

    def fallback_pdp_url(self, article: str) -> str:
        return self.search_url(article)
