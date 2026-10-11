from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.roco.parse_pdp import (
    _normalize_electric,
    _operator_country,
    _parse_title,
    parse_roco_pdp,
)
from locobox_cli.adapters.sources.shop_site import RocoShopSite, shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle

FIXTURE = Path(__file__).parent / "fixtures" / "roco_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_roco_shop_site_pdp_url() -> None:
    site = RocoShopSite()
    assert site.is_pdp_url(
        "https://www.roco.cc/rde/produkte/lokomotiven/dampflokomotiven/70035-dampflokomotive-t3-kpev.html",
        "70035",
    )
    assert site.is_pdp_url(
        "https://www.roco.cc/rde/produkte/lokomotiven/dampflokomotiven/"
        "7180012-dampflokomotive-455-244-csd.html#contentarea",
        "7180012",
    )
    assert not site.is_pdp_url(
        "https://www.roco.cc/rde/catalogsearch/result/?q=70035", "70035"
    )
    assert "catalogsearch" in shop_site_for("roco").search_url("70035")


def test_operator_country_no_false_prefix() -> None:
    assert _operator_country("SNCF") == ("SNCF", "FR")
    assert _operator_country("DRG") == ("DRG", "DE")
    assert _operator_country("DB AG") == ("DB AG", "DE")
    assert _operator_country("NS") == ("NS", "NL")
    assert _operator_country("DB Cargo") == ("DB", "DE")


def test_dr_country_by_era() -> None:
    assert _operator_country("DR", era="IV") == ("DR", "DD")
    assert _operator_country("DR", era="V") == ("DR", "DD")
    assert _operator_country("DR", era="III") == ("DR", "DE")
    assert _operator_country("DR", era="I-III") == ("DR", "DE")
    assert _operator_country("DR", era="") == ("DR", "DD")


def test_normalize_electric_roco_values() -> None:
    assert _normalize_electric("DCC") == "DC-Digital"
    assert _normalize_electric("Wechselstrom") == "AC-Digital"
    assert _normalize_electric("Wechselstrom Analog") == "AC-Analog"
    assert _normalize_electric("AC Digital") == "AC-Digital"
    assert _normalize_electric("MFX") == "DC-Digital"
    assert _normalize_electric("DC Analog") == "DC-Analog"
    assert _normalize_electric("Gleichstrom Digital") == "DC-Digital"


def test_title_longest_prefix() -> None:
    typ, op, cats = _parse_title("7000123 Elektrotriebzug ICE 4, DB AG")
    assert typ == "ICE 4"
    assert op == "DB AG"
    assert "elektrotriebzug" in cats
    typ2, _, cats2 = _parse_title("Nahverkehrs-Steuerwagen Bnrdzf, DB")
    assert typ2 == "Bnrdzf"
    assert "nahverkehrs-steuerwagen" in cats2


def test_parse_roco_pdp_fixture_schema_valid() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    art = parse_roco_pdp(
        html,
        canonical_url="https://www.roco.cc/rde/produkte/lokomotiven/dampflokomotiven/70035-dampflokomotive-t3-kpev.html",
        article="70035",
        campaign_tag="roco-neuheiten-2024",
    )
    assert art["articleNumber"] == "70035"
    assert art["manufacturer"] == "Roco"
    assert art["uvp"]["amount"] == 277.9
    assert "dampflokomotive" in art["categories"]
    assert art["model"]["era"]
    assert art["model"]["scale"] == "H0"
    assert art["model"]["type"] == "T3"
    assert art["model"]["operator"] in {"K.P.E.V.", "KPEV"}
    issues = ValidateArticle.from_contracts(REPO).run(art)
    assert issues == [], issues


def test_parse_roco_pdp_zero_price_uvp_null() -> None:
    html = FIXTURE.read_text(encoding="utf-8").replace(
        'content="277.9"', 'content="0"'
    )
    art = parse_roco_pdp(
        html,
        canonical_url="https://www.roco.cc/rde/produkte/lokomotiven/dampflokomotiven/70035-dampflokomotive-t3-kpev.html",
        article="70035",
    )
    assert art["uvp"] is None
    issues = ValidateArticle.from_contracts(REPO).run(art)
    assert issues == [], issues


def test_parse_roco_pdp_article_mismatch() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    try:
        parse_roco_pdp(
            html,
            canonical_url="https://www.roco.cc/rde/produkte/lokomotiven/dampflokomotiven/70035-dampflokomotive-t3-kpev.html",
            article="99999",
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "70035" in str(exc)
