from __future__ import annotations

from typing import Any, Optional


def parse_acme_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
) -> dict[str, Any]:
    """
    ACME has no HTML product detail page.

    Product data lives in flyer PDFs (``…/files/AC{article}.pdf``). This stub
    refuses HTML parse so callers fail clearly instead of inventing fields.
    """
    del html, canonical_url, campaign_tag  # unused — no HTML PDP yet
    raise NotImplementedError(
        f"ACME PDP parse is not implemented for article {article!r}: "
        "there is no stable HTML shop page; use flyer PDFs at "
        f"https://www.acmetreni.it/files/AC{article}.pdf (flyer parse pending)."
    )
