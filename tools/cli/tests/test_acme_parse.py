from __future__ import annotations

from pathlib import Path

import pytest

from locobox_cli.adapters.sources.acme.parse_pdp import parse_acme_flyer, parse_acme_pdp

FIXTURE = Path(__file__).parent / "fixtures" / "acme_flyer_60655.txt"


def test_parse_acme_flyer_dc_and_sound() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    dc = parse_acme_flyer(
        text,
        canonical_url="https://www.acmetreni.it/files/AC60655.pdf",
        article="60655",
        campaign_tag="acme-herbstneuheiten-2026",
    )
    assert dc["id"] == "acme-60655"
    assert dc["manufacturer"] == "ACME"
    assert dc["articleNumber"] == "60655"
    assert dc["uvp"]["amount"] == 212.0
    assert dc["model"]["scale"] == "H0"
    assert dc["model"]["operator"] == "SBB"
    assert dc["model"]["country"] == "CH"
    assert dc["model"]["electricSystem"] == "DC-Analog"
    assert "Zürich" in dc["description"] or "Zuerich" in dc["description"]
    assert dc["tags"] == ["acme-herbstneuheiten-2026"]
    assert dc["releaseDate"] == "2026"
    assert dc["source"]["url"].endswith("AC60655.pdf")

    sound = parse_acme_flyer(
        text,
        canonical_url="https://www.acmetreni.it/files/AC60655.pdf",
        article="69655",
        campaign_tag="acme-herbstneuheiten-2026",
        uvp_amount=212.0,
    )
    assert sound["articleNumber"] == "69655"
    assert sound["model"]["electricSystem"] == "DC-Digital"
    assert sound["uvp"]["amount"] == 212.0


def test_parse_acme_pdp_rejects_bare_html() -> None:
    with pytest.raises(NotImplementedError):
        parse_acme_pdp(
            "<!DOCTYPE html><html><body>no sku</body></html>",
            canonical_url="https://www.acmetreni.it/",
            article="60655",
        )
