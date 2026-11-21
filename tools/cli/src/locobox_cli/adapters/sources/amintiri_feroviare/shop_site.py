from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus


def normalize_article(article: str) -> str:
    """Strip optional AF prefix; keep leading L for SKUs like L131526."""
    raw = article.strip()
    if raw.upper().startswith("AF") and len(raw) > 2 and raw[2:].replace("-", "").isalnum():
        return raw[2:].lstrip("-")
    return raw


@dataclass(frozen=True, slots=True)
class AmintiriFeroviareShopSite:
    """Official Magento-like shop on amintiriferoviare.com (AF Models)."""

    slug: str = "amintiri-feroviare"

    def search_url(self, article: str) -> str:
        art = normalize_article(article)
        return f"https://www.amintiriferoviare.com/cauta?caut={quote_plus(art)}"

    def menzels_search_url(self, article: str) -> str:
        art = normalize_article(article)
        q = art if art.upper().startswith("L") else f"AF{art}"
        return f"https://www.menzels-lokschuppen.de/search?search={quote_plus(q)}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0]
        host_path = u.lower()
        art = normalize_article(article).lower()
        af = f"af{art}"
        if "amintiriferoviare.com" in host_path and "/produs/" in host_path:
            slug = host_path.split("/produs/", 1)[-1]
            return (
                slug.startswith(f"{art}-")
                or slug.startswith(f"hgd{art}-")
                or slug.startswith(f"l{art.lstrip('l')}-")
                or f"af{art}" in slug
                or art in slug.split("-")[0]
            )
        if "menzels-lokschuppen.de" in host_path:
            return af in host_path or f"/{art}" in host_path
        return False

    def fallback_pdp_url(self, article: str) -> str:
        return self.search_url(article)
