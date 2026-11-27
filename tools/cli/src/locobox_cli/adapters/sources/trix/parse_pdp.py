"""Trix Produktdatenbank PDP parser.

``trix.de`` serves the same product-database HTML as ``maerklin.de`` (H1, Vorbild/Modell
paragraphs, spec table, ``static.maerklin.de`` photos), so everything except brand, id and
the DC power system is shared with :mod:`locobox_cli.adapters.sources.maerklin.parse_pdp`.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from locobox_cli.adapters.sources.maerklin.parse_pdp import parse_maerklin_pdp


# Trix-only operator hints, tried only when the shared Märklin rules left ``Unbekannt``.
_EXTRA_OPERATORS: list[tuple[str, str, str]] = [
    (r"Dispolok", "Siemens Dispolok", "DE"),
    (r"im\s+Design\s+für\s+den\s+Film|\bFilm\s+[\"„]", "Fiktiv", "DE"),
    (r"Gleisbau-Firma|Privatbahn-Lokomotive|Museumslokomotive", "Privatbahn", "DE"),
    (r"preussische[nr]?\s+(?:\w+\s+)?(?:Nebenbahn|Lokomotive|Gattung)", "KPEV", "DE"),
]


def parse_trix_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    raw = parse_maerklin_pdp(
        html,
        canonical_url=canonical_url,
        article=article,
        campaign_tag=campaign_tag,
        uvp_amount=uvp_amount,
    )
    model = raw["model"]
    if model["operator"] == "Unbekannt":
        for pat, op, cc in _EXTRA_OPERATORS:
            if re.search(pat, raw["description"], re.I):
                model["operator"], model["country"] = op, cc
                break
    raw["id"] = f"trix-{raw['articleNumber']}"
    raw["manufacturer"] = "Trix"
    raw["source"]["notes"] = "Daten von der Trix-Produktdatenbank, automatisch geupdated."
    # Märklin H0 is AC (3-rail); Trix H0 is DC (2-rail).
    model["electricSystem"] = model["electricSystem"].replace("AC-", "DC-")
    return raw
