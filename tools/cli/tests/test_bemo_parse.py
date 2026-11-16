from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.bemo.parse_pdp import parse_bemo_pdp
from locobox_cli.adapters.sources.bemo.shop_site import BemoShopSite, spaced_sku
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle
from locobox_cli.domain.manufacturer import Manufacturer

FIXTURE = Path(__file__).parent / "fixtures" / "bemo_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_spaced_sku_four_plus_three() -> None:
    assert spaced_sku("1258168") == "1258 168"
    assert spaced_sku("1258 168") == "1258 168"
    assert spaced_sku("2295561") == "2295 561"


def test_bemo_shop_site_search_and_pdp() -> None:
    site = BemoShopSite()
    url = site.search_url("1258168")
    assert "bemo-modellbahn.de/?s=" in url
    assert "1258168" in url
    assert "1258+168" not in url
    spaced = site.spaced_search_url("1258168")
    assert "1258+168" in spaced
    pdp = "https://www.bemo-modellbahn.de/produkt/elektrolok-ge-4-4-iii-rhb-2295-561/"
    assert site.is_pdp_url(pdp, "2295561")
    assert site.is_pdp_url(pdp, "9999999")
    assert not site.is_pdp_url(
        "https://www.bemo-modellbahn.de/?s=1258+168", "1258168"
    )
    assert not site.is_pdp_url(
        "https://www.bemo-modellbahn.de/kategorie/lokomotiven/", "1258168"
    )
    assert site.fallback_pdp_url("1258168") == site.search_url("1258168")
    assert shop_site_for("bemo").slug == "bemo"
    assert Manufacturer.parse("bemo").display_name == "BEMO"


def test_parse_bemo_pdp_sample() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    art = parse_bemo_pdp(
        html,
        canonical_url=(
            "https://www.bemo-modellbahn.de/produkt/"
            "elektrolok-ge-4-4-iii-rhb-2295-561/"
        ),
        article="2295561",
        campaign_tag="bemo-neuheiten-2026",
    )
    assert art["manufacturer"] == "BEMO"
    assert art["articleNumber"] == "2295561"
    assert art["id"] == "bemo-2295561"
    assert art["uvp"]["amount"] == 89.99
    assert art["model"]["scale"] == "H0m"
    assert art["model"]["era"] == "VI"
    assert art["model"]["operator"] == "RhB"
    assert art["model"]["country"] == "CH"
    assert art["model"]["electricSystem"] == "DC-Digital"
    assert "elektrolokomotive" in art["categories"]
    assert art["source"]["url"].startswith("https://www.bemo-modellbahn.de/produkt/")
    assert art["source"]["imageUrl"].startswith("https://www.bemo-modellbahn.de/")
    assert "bemo-neuheiten-2026" in art["tags"]
    assert "ß" not in art["description"]
    ValidateArticle.from_contracts(REPO).assert_valid(art)


def test_parse_bemo_pdp_article_mismatch() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    try:
        parse_bemo_pdp(
            html,
            canonical_url="https://www.bemo-modellbahn.de/produkt/x/",
            article="1258168",
        )
    except ValueError as exc:
        assert "2295561" in str(exc)
        assert "1258168" in str(exc)
    else:
        raise AssertionError("expected ValueError for article mismatch")
