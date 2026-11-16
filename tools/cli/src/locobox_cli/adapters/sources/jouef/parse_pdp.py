from __future__ import annotations

from typing import Any, Optional

from locobox_cli.adapters.sources.jouef.shop_site import JouefShopNotImplementedError


def parse_jouef_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
) -> dict[str, Any]:
    """Placeholder until a stable Jouef/Hornby PDP HTML shape is confirmed."""
    del html, canonical_url, campaign_tag  # unused until implemented
    raise JouefShopNotImplementedError(
        "Jouef PDP parse is not implemented yet; use catalog extract for "
        f"{article!r} and enrich manually or wait for shop wiring."
    )
