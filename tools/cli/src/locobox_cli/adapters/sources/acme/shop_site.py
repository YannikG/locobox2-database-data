from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AcmeFlyerSite:
    """
    ACME has no HTML webshop / stable PDP.

    Product sheets are flyer PDFs under ``/files/AC{article}.pdf`` on
    acmetreni.it. ``shop fetch`` can open that URL; HTML PDP parse is not
    implemented (flyer PDF parse is future work).
    """

    slug: str = "acme"

    def flyer_url(self, article: str) -> str:
        art = article.strip()
        if art.upper().startswith("AC") and art[2:].isdigit():
            art = art[2:]
        return f"https://www.acmetreni.it/files/AC{art}.pdf"

    def search_url(self, article: str) -> str:
        # Direct flyer: there is no catalog search on acmetreni.it.
        return self.flyer_url(article)

    def is_pdp_url(self, href: str, article: str) -> bool:
        if not href or not href.startswith("http"):
            return False
        u = href.split("#", 1)[0].split("?", 1)[0].lower()
        art = article.strip().lower()
        if art.startswith("ac") and art[2:].isdigit():
            art = art[2:]
        return "acmetreni.it" in u and f"/files/ac{art}.pdf" in u

    def fallback_pdp_url(self, article: str) -> str:
        return self.flyer_url(article)
