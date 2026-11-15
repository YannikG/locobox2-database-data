from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LimaModelSite:
    """
    Official Lima Expert shop on limamodel.it (Hornby International).

    PDP URLs look like ``/products/{slug}-{sku}`` (SKU lowercased at the end),
    e.g. ``…/products/fs-trenitalia-e464-…-hl2664``. The marketing slug is not
    constructible from the article number alone, so fetch starts at site search
    (same idea as Roco catalogsearch / Trix when no short product-db path exists).

    Note: ``/search?query={SKU}`` often returns empty for out-of-stock or older
    items even when the PDP still exists. CloakBrowser then fails with
    ``no_pdp_link``; resolve the PDP from Neuheiten/catalog pages or paste HTML
    under ``.tmp/import/{campaign}/html/{SKU}.html`` and run ``shop parse``.
    """

    slug: str = "lima"
    base: str = "https://it.limamodel.it"

    def search_url(self, article: str) -> str:
        art = article.strip()
        return f"{self.base}/search?query={art}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0].lower()
        if "limamodel.it" not in u or "/products/" not in u:
            return False
        art = article.strip().lower()
        # PDP path ends with ``-{sku}`` (Hornby concrete5 storefront).
        return u.rstrip("/").endswith(f"-{art}") or f"-{art}" in u.split("/")[-1]

    def fallback_pdp_url(self, article: str) -> str:
        # No stable short PDP by SKU alone; search is the documented entry point.
        return self.search_url(article)
