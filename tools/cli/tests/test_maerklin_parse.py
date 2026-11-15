from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.maerklin.parse_pdp import parse_maerklin_pdp
from locobox_cli.adapters.sources.maerklin.shop_site import MaerklinProductDbSite
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.application.articles.validate import ValidateArticle

FIXTURE = Path(__file__).parent / "fixtures" / "maerklin_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_maerklin_shop_site_direct_pdp() -> None:
    site = MaerklinProductDbSite()
    url = site.search_url("39661")
    assert url.endswith("/article/39661")
    assert site.is_pdp_url(url, "39661")
    assert not site.is_pdp_url(url, "38477")
    assert shop_site_for("maerklin").slug == "maerklin"
    assert shop_site_for("marklin").slug == "maerklin"


def test_parse_maerklin_pdp_sample() -> None:
    html = FIXTURE.read_text(encoding="utf-8", errors="replace")
    art = parse_maerklin_pdp(
        html,
        canonical_url="https://www.maerklin.de/de/produkte/details/article/39661",
        article="39661",
        campaign_tag="maerklin-neuheiten-2026",
        uvp_amount=699.0,
    )
    assert art["manufacturer"] == "Maerklin"
    assert art["articleNumber"] == "39661"
    assert art["id"] == "maerklin-39661"
    assert art["uvp"]["amount"] == 699.0
    assert art["model"]["scale"] == "H0"
    assert art["model"]["era"] == "III"
    assert art["model"]["operator"] == "DB"
    assert art["model"]["country"] == "DE"
    assert art["model"]["electricSystem"] == "AC-Digital"
    assert "Dampflokomotive" in art["model"]["type"]
    assert art["source"]["imageUrl"].startswith("https://static.maerklin.de/")
    assert "maerklin-neuheiten-2026" in art["tags"]
    ValidateArticle.from_contracts(REPO).assert_valid(art)
