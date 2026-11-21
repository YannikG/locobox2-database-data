from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.amintiri_feroviare.parse_pdp import (
    parse_amintiri_feroviare_pdp,
)
from locobox_cli.adapters.sources.amintiri_feroviare.shop_site import (
    AmintiriFeroviareShopSite,
    normalize_article,
)
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle
from locobox_cli.domain.manufacturer import Manufacturer

FIXTURE = Path(__file__).parent / "fixtures" / "amintiri_feroviare_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_normalize_article_strips_af_prefix() -> None:
    assert normalize_article("AF10024") == "10024"
    assert normalize_article("10024") == "10024"
    assert normalize_article("L131526") == "L131526"


def test_amintiri_shop_site_search_and_pdp() -> None:
    site = AmintiriFeroviareShopSite()
    assert "cauta?caut=10024" in site.search_url("10024")
    assert "AF10201" in site.menzels_search_url("10201")
    pdp = "https://www.amintiriferoviare.com/produs/10024-locomotiva-electrica-atc-060-ea-93"
    assert site.is_pdp_url(pdp, "10024")
    assert not site.is_pdp_url(
        "https://www.amintiriferoviare.com/catalog-categorie/locomotive-electrice",
        "10024",
    )
    menzels = "https://www.menzels-lokschuppen.de/af-models-af10201-vtr-e-lok-transmontana-ep-6"
    assert site.is_pdp_url(menzels, "10201")
    assert shop_site_for("af").slug == "amintiri-feroviare"
    assert Manufacturer.parse("af").display_name == "Amintiri Feroviare"
    assert Manufacturer.parse("amintiri-feroviare").slug == "amintiri-feroviare"


def test_parse_amintiri_official_sample() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    art = parse_amintiri_feroviare_pdp(
        html,
        canonical_url=(
            "https://www.amintiriferoviare.com/produs/"
            "10024-locomotiva-electrica-atc-060-ea-93"
        ),
        article="10024",
        campaign_tag="amintiri-feroviare-katalog-2026",
    )
    assert art["manufacturer"] == "Amintiri Feroviare"
    assert art["articleNumber"] == "10024"
    assert art["id"] == "amintiri-feroviare-10024"
    assert art["model"]["scale"] == "H0"
    assert art["model"]["era"] == "VI"
    assert art["model"]["operator"] in {"ATC", "CFR", "Astra Trans Carpatic"}
    assert art["model"]["country"] == "RO"
    assert "elektrolokomotive" in art["categories"]
    assert art["source"]["url"].startswith("https://www.amintiriferoviare.com/produs/")
    assert "amintiri-feroviare-katalog-2026" in art["tags"]
    assert "ß" not in art["description"]
    ValidateArticle.from_contracts(REPO).assert_valid(art)
