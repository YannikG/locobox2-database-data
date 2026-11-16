from __future__ import annotations

from dataclasses import dataclass


class JouefShopNotImplementedError(NotImplementedError):
    """Raised when Jouef shop fetch/parse is requested before PDP wiring exists."""


@dataclass(frozen=True, slots=True)
class JouefShopSite:
    """Stub for fr.jouef.com / uk.jouef.com (Hornby Magento).

    Catalog extract works; live shop fetch/parse is not wired yet because the
    official catalogue pages are often empty and PDP URL patterns are unstable.
    """

    slug: str = "jouef"

    def search_url(self, article: str) -> str:
        raise JouefShopNotImplementedError(
            "Jouef shop fetch is not implemented yet; use catalog extract "
            f"(--source jouef) for {article!r}. Official fr/uk.jouef.com PDPs "
            "are not wired."
        )

    def is_pdp_url(self, href: str, article: str) -> bool:
        return False

    def fallback_pdp_url(self, article: str) -> str:
        raise JouefShopNotImplementedError(
            "Jouef shop parse is not implemented yet; no stable PDP URL for "
            f"{article!r}."
        )
