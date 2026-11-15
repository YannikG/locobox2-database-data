from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.ree.parse_pdp import parse_ree_pdp
from locobox_cli.adapters.sources.ree.shop_site import ReeShopSite
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle
from locobox_cli.application.queue.parse import parse_queue_text

FIXTURE = Path(__file__).parent / "fixtures" / "ree_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_ree_shop_site_search_and_pdp() -> None:
    site = ReeShopSite()
    url = site.search_url("MB-263S")
    assert "ree-store.com/recherche" in url
    assert "s=MB263S" in url
    pdp = (
        "https://www.ree-store.com/locomotives-electriques/"
        "3880--ho-bb-9317-digital-sound-mb263s-0652733591197.html"
    )
    assert site.is_pdp_url(pdp, "MB-263S")
    assert site.is_pdp_url(pdp, "MB263S")
    assert not site.is_pdp_url(pdp, "MB-263")
    assert not site.is_pdp_url(
        "https://www.ree-store.com/recherche?controller=search&s=MB263S", "MB-263S"
    )
    assert shop_site_for("ree").slug == "ree"


def test_parse_ree_pdp_sample() -> None:
    html = FIXTURE.read_text(encoding="utf-8", errors="replace")
    art = parse_ree_pdp(
        html,
        canonical_url=(
            "https://www.ree-store.com/locomotives-electriques/"
            "3880--ho-bb-9317-digital-sound-mb263s-0652733591197.html"
        ),
        article="MB-263S",
        campaign_tag="ree-neuheiten-2026",
    )
    assert art["manufacturer"] == "REE"
    assert art["articleNumber"] == "MB-263S"
    assert art["id"] == "ree-MB-263S"
    assert art["uvp"]["amount"] == 374.17
    assert art["model"]["scale"] == "H0"
    assert art["model"]["era"] == "III-IV"
    assert art["model"]["operator"] == "SNCF"
    assert art["model"]["country"] == "FR"
    assert art["model"]["electricSystem"] == "DC-Digital"
    assert art["model"]["type"] == "BB 9300"
    assert art["model"]["number"] == "BB 9317"
    assert art["categories"] == ["lokomotive", "elektrolokomotive"]
    assert art["source"]["imageUrl"].startswith("https://www.ree-store.com/")
    assert "ree-neuheiten-2026" in art["tags"]
    ValidateArticle.from_contracts(REPO).assert_valid(art)


def test_queue_accepts_ree_article_numbers() -> None:
    doc = parse_queue_text("MB 176S\nMB-263S\tElektrolok\tmotorized\t374,17 EUR\n")
    assert [e.article.value for e in doc.entries] == ["MB-176S", "MB-263S"]
    assert doc.entries[1].kind == "Elektrolok"
    assert doc.entries[1].price_eur == 374.17
