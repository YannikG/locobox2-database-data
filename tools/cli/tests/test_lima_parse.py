from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.lima.parse_pdp import parse_lima_pdp
from locobox_cli.adapters.sources.lima.shop_site import LimaModelSite
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle

FIXTURE = Path(__file__).parent / "fixtures" / "lima_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_lima_shop_site_search_and_pdp() -> None:
    site = LimaModelSite()
    assert site.search_url("HL2664") == "https://it.limamodel.it/search?query=HL2664"
    pdp = (
        "https://it.limamodel.it/products/"
        "fs-trenitalia-e464-464-special-livery-quattroseiquattro-ep-vi-hl2664"
    )
    assert site.is_pdp_url(pdp, "HL2664")
    assert site.is_pdp_url(pdp, "hl2664")
    assert not site.is_pdp_url(pdp, "HL2665")
    assert site.fallback_pdp_url("HL2664") == site.search_url("HL2664")
    assert shop_site_for("lima").slug == "lima"


def test_parse_lima_pdp_sample() -> None:
    html = FIXTURE.read_text(encoding="utf-8", errors="replace")
    art = parse_lima_pdp(
        html,
        canonical_url=(
            "https://it.limamodel.it/products/"
            "fs-trenitalia-e464-464-special-livery-quattroseiquattro-ep-vi-hl2664"
        ),
        article="HL2664",
        campaign_tag="lima-neuheiten-2024",
    )
    assert art["manufacturer"] == "Lima"
    assert art["articleNumber"] == "HL2664"
    assert art["id"] == "lima-HL2664"
    assert art["uvp"]["amount"] == 173.9
    assert art["model"]["scale"] == "H0"
    assert art["model"]["era"] == "VI"
    assert art["model"]["operator"] == "FS"
    assert art["model"]["country"] == "IT"
    assert art["model"]["electricSystem"] == "DC-Analog"
    assert art["model"]["minRadiusMm"] == 356.5
    assert "locomotiva elettrica" in art["model"]["type"].lower()
    assert art["source"]["url"].endswith("-hl2664")
    assert art["source"]["imageUrl"].startswith("https://d63oxfkn1m8sf.cloudfront.net/")
    assert "lima-neuheiten-2024" in art["tags"]
    assert art["releaseDate"] == "2024"
    ValidateArticle.from_contracts(REPO).assert_valid(art)


def test_parse_lima_pdp_article_mismatch() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    try:
        parse_lima_pdp(
            html,
            canonical_url=(
                "https://it.limamodel.it/products/"
                "fs-trenitalia-e464-464-special-livery-quattroseiquattro-ep-vi-hl2664"
            ),
            article="HL9999",
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "HL2664" in str(exc)
