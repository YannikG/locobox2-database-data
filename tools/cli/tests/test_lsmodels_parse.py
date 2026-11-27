from __future__ import annotations

from pathlib import Path

import pytest

from locobox_cli.adapters.sources.lsmodels.parse_pdp import (
    _normalize_electric,
    _normalize_scale,
    parse_lsmodels_pdp,
)
from locobox_cli.adapters.sources.lsmodels.shop_site import LsModelsShopSite
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle
from locobox_cli.domain.manufacturer import Manufacturer

FIXTURE = Path(__file__).parent / "fixtures" / "lsmodels_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_lsmodels_shop_site_search_and_pdp() -> None:
    site = LsModelsShopSite()
    assert "s=16075" in site.search_url("16075")
    assert "s=16075" in site.search_url("16 075")
    assert site.is_pdp_url(
        "https://lsmodels.eu/de/ausverkauft/2192-db-cargo-vectron-ms-white-i-am-einziganders.html",
        "16075",
    )
    assert site.is_pdp_url(
        "https://lsmodels.eu/en/sold-out/2192-db-cargo-vectron-ms-white-i-am-einziganders.html",
        "99999",
    )
    assert not site.is_pdp_url(
        "https://lsmodels.eu/de/suche?controller=search&s=16075",
        "16075",
    )
    assert not site.is_pdp_url(
        "https://lsmodels.eu/de/33-ausverkauft",
        "16075",
    )
    assert shop_site_for("lsmodels").slug == "lsmodels"
    assert shop_site_for("LS Models").slug == "lsmodels"
    assert Manufacturer.parse("lsmodels").display_name == "LS Models"


def test_normalize_scale_and_electric() -> None:
    assert _normalize_scale("HO") == "H0"
    assert _normalize_scale("H0") == "H0"
    assert _normalize_electric("DC") == "DC-Analog"
    assert _normalize_electric("AC") == "AC-Digital"


def test_parse_lsmodels_pdp_sample() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    art = parse_lsmodels_pdp(
        html,
        canonical_url=(
            "https://lsmodels.eu/de/ausverkauft/"
            "2192-db-cargo-vectron-ms-white-i-am-einziganders.html"
        ),
        article="16075",
        campaign_tag="lsmodels-neuheiten-2024",
    )
    assert art["manufacturer"] == "L.S.Models"
    assert art["id"] == "lsmodels-16075"
    assert art["articleNumber"] == "16075"
    assert art["uvp"] is None
    assert art["model"]["scale"] == "H0"
    assert art["model"]["era"] == "VI"
    assert art["model"]["electricSystem"] == "DC-Analog"
    assert art["model"]["operator"] == "DB Cargo"
    assert art["model"]["country"] == "DE"
    assert "elektrolokomotive" in art["categories"]
    assert art["source"]["imageUrl"].startswith("https://lsmodels.eu/")
    assert "lsmodels.eu" in art["source"]["notes"]
    assert "lsmodels-neuheiten-2024" in art["tags"]
    ValidateArticle.from_contracts(REPO).assert_valid(art)


def test_parse_lsmodels_pdp_article_mismatch() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    try:
        parse_lsmodels_pdp(
            html,
            canonical_url="https://lsmodels.eu/de/ausverkauft/2192-x.html",
            article="99999",
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "16075" in str(exc)


def test_parse_lsmodels_pdp_with_uvp_from_queue() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    art = parse_lsmodels_pdp(
        html,
        canonical_url="https://lsmodels.eu/de/ausverkauft/2192-x.html",
        article="16075",
        uvp_amount=189.0,
    )
    assert art["uvp"] == {"amount": 189.0, "currency": "EUR"}


def test_canon_reference_strips_dc_ac_sound() -> None:
    from locobox_cli.adapters.sources.lsmodels.parse_pdp import _canon_reference

    assert _canon_reference("13001 DC") == "13001"
    assert _canon_reference("13001 AC S") == "13001"
    assert _canon_reference("16 075") == "16075"


def test_split_lsmodels_title_common_patterns() -> None:
    from locobox_cli.adapters.sources.lsmodels.parse_pdp import (
        split_lsmodels_title,
        _operator_from_title,
    )

    assert split_lsmodels_title(
        "1312, Grau-blau, Linien türkis, LINEAS, Version 2020",
        categorie="HLE 13",
    ) == ("HLE 13", "1312", "Grau-blau, Linien türkis, LINEAS, Version 2020")
    assert split_lsmodels_title("BB 22200, grau/violett, En Voyage")[0] == "BB 22200"
    typ, num, liv = split_lsmodels_title("X4630, rouge crème, Longeau")
    assert (typ, num, liv) == ("X 4500", "X 4630", "rouge crème, Longeau")
    typ, num, _liv = split_lsmodels_title("X4638-XR8650,bleu, TER SNCF, Nevers")
    assert (typ, num) == ("X 4500", "X 4638")
    typ, num, _liv = split_lsmodels_title(
        "Z 27877, blau/metallic grau, Alsace, vierteilig, DB Zulassung"
    )
    assert typ == "AGC" and num == "27877"
    typ, num, liv = split_lsmodels_title(
        'DB Cargo Vectron MS, white, "I am Einziganders"'
    )
    assert typ == "Vectron MS" and num is None and liv == "I am Einziganders"
    assert split_lsmodels_title("1347 blanche / wit (SNCB / NMBS)")[:2] == (
        "HLE 13",
        "1347",
    )
    assert _operator_from_title("BB 22200, x", "SNCF") == ("SNCF", "FR")


def test_parse_lsmodels_pdp_sample_splits_vectron_type() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    art = parse_lsmodels_pdp(
        html,
        canonical_url=(
            "https://lsmodels.eu/de/ausverkauft/"
            "2192-db-cargo-vectron-ms-white-i-am-einziganders.html"
        ),
        article="16075",
    )
    assert art["model"]["type"] == "Vectron MS"
    assert art["model"]["livery"] == "I am Einziganders"


def test_parse_lsmodels_pdp_rejects_pantograph_accessory() -> None:
    html = (
        "<html><head><title>x</title></head><body>"
        "<h1>Set 4 AM 18 Fahrstromabnehmer, 2x 3000 V DC</h1></body></html>"
    )
    with pytest.raises(ValueError, match="Zubehör"):
        parse_lsmodels_pdp(html, canonical_url="https://lsmodels.eu/x.html", article="89206")
