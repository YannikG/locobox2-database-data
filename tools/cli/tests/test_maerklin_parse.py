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


def test_parse_generic_h1_uses_vorbild_and_spaced_operator() -> None:
    html = """
    <h1>Elektrolokomotive</h1>
    <p><b>Vorbild:</b> Elektrolokomotive Baureihe E 186 der Niederländischen Eisenbahnen ( NS ).</p>
    <p><b>Modell:</b> Mit Digital-Decoder mfx.</p>
    <table>
      <tr><th>Art.Nr.</th><td>36622</td></tr>
      <tr><th>Spur / Bauart</th><td>H0</td></tr>
      <tr><th>Epoche</th><td>VI</td></tr>
    </table>
    """
    art = parse_maerklin_pdp(
        html,
        canonical_url="https://www.maerklin.de/de/produkte/details/article/36622",
        article="36622",
        campaign_tag="maerklin-neuheiten-2015",
        uvp_amount=199.95,
    )
    assert art["model"]["type"] == "Baureihe E 186"
    assert art["model"]["operator"] == "NS"
    assert art["model"]["country"] == "NL"
    ValidateArticle.from_contracts(REPO).assert_valid(art)


def test_operator_from_vorbild_named_roads() -> None:
    from locobox_cli.adapters.sources.maerklin.parse_pdp import _operator_from_vorbild

    assert _operator_from_vorbild("Union Pacific Railroad (U.P.).") == ("UP", "US")
    assert _operator_from_vorbild("Hector Rail Vectron BR 193") == ("Hector Rail", "SE")
    assert _operator_from_vorbild("Königlich Preussischen Eisenbahn-Verwaltung (KPEV)")[0] == "KPEV"
