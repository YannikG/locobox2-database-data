from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MaerklinProductDbSite:
    """Märklin Produktdatenbank on maerklin.de (reliable by article number for Neuheiten)."""

    slug: str = "maerklin"

    def search_url(self, article: str) -> str:
        return f"https://www.maerklin.de/de/produkte/details/article/{article}"

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0].lower()
        art = article.strip().lower()
        return "maerklin.de" in u and f"/produkte/details/article/{art}" in u

    def fallback_pdp_url(self, article: str) -> str:
        return self.search_url(article)
