from __future__ import annotations

from locobox_cli.adapters.shop_cloakbrowser import (
    _html_has_article_sku,
    _is_piko_artikel_url,
)


def test_html_has_article_sku_markers() -> None:
    html = (
        '<p>Artikelnummer: <span>21782</span></p>'
        '{"sku":"21782","gtin13":"4015615217824"}'
    )
    assert _html_has_article_sku(html, "21782")
    assert not _html_has_article_sku(html, "2178")
    assert not _html_has_article_sku(html, "51274")


def test_is_piko_artikel_url() -> None:
    assert _is_piko_artikel_url(
        "https://www.piko-shop.de/de/artikel/e-lok-e-17-dr-iii-51274.html"
    )
    assert not _is_piko_artikel_url(
        "https://www.piko-shop.de/de/praesenz/search.html?q=21782"
    )
    assert not _is_piko_artikel_url("https://www.roco.cc/rde/foo-21782.html")
