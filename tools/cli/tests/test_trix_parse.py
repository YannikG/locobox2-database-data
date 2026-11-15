from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.adapters.sources.trix.parse_pdp import parse_trix_pdp
from locobox_cli.adapters.sources.trix.shop_site import TrixProductDbSite
from locobox_cli.application.articles.validate import ValidateArticle

FIXTURE = Path(__file__).parent / "fixtures" / "trix_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_trix_shop_site_direct_pdp() -> None:
    site = TrixProductDbSite()
    url = site.search_url("25061")
    assert url.endswith("/article/25061")
    assert site.is_pdp_url(url, "25061")
    assert not site.is_pdp_url(url, "22380")
    assert shop_site_for("trix").slug == "trix"


def test_parse_trix_pdp_sample() -> None:
    html = FIXTURE.read_text(encoding="utf-8", errors="replace")
    art = parse_trix_pdp(
        html,
        canonical_url="https://www.trix.de/de/produkte/details/article/25061",
        article="25061",
        campaign_tag="trix-neuheiten-2026",
        uvp_amount=699.0,
    )
    assert art["manufacturer"] == "Trix"
    assert art["articleNumber"] == "25061"
    assert art["uvp"]["amount"] == 699.0
    assert art["model"]["scale"] == "H0"
    assert art["model"]["era"] == "III"
    assert art["model"]["operator"] == "DB"
    assert art["model"]["country"] == "DE"
    assert art["model"]["electricSystem"] == "DC-Digital"
    assert "Dampflokomotive" in art["model"]["type"]
    assert art["source"]["imageUrl"].startswith("https://static.maerklin.de/")
    assert "trix-neuheiten-2026" in art["tags"]
    ValidateArticle.from_contracts(REPO).assert_valid(art)
