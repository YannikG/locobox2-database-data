from __future__ import annotations

from pathlib import Path

import pytest

from locobox_cli.adapters.sources.jouef.catalog import (
    extract_jouef_catalog_rows,
    rows_to_queue,
)
from locobox_cli.adapters.sources.jouef.parse_pdp import parse_jouef_pdp
from locobox_cli.adapters.sources.jouef.shop_site import (
    JouefShopNotImplementedError,
    JouefShopSite,
)
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.domain.article import ArticleNumber

FIXTURE = Path(__file__).parent / "fixtures" / "jouef_catalog_snippet.txt"


def test_extract_locomotives_skips_coaches_and_wagons() -> None:
    rows = extract_jouef_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "HJ2461" in arts
    assert "HJ2461S" in arts
    assert "HJ2342" in arts
    assert "HJ2471" in arts
    assert "HJ2471S" in arts
    assert "HJ4205" not in arts
    assert "HJ6290" not in arts
    by_art = {r.article: r for r in rows}
    assert by_art["HJ2461"].section == "locomotive"
    assert by_art["HJ2461"].kind == "Diesellok"
    assert by_art["HJ2342"].kind == "Diesellok"


def test_extract_all_rolling_stock_includes_coaches() -> None:
    rows = extract_jouef_catalog_rows(
        FIXTURE.read_text(encoding="utf-8"), locomotives_only=False
    )
    arts = {r.article for r in rows}
    assert "HJ4205" in arts
    assert "HJ6290" in arts
    # HJ4206HM is outside HJ#### / HJ####S; must not yield a truncated HJ4206
    assert "HJ4206HM" not in arts
    assert "HJ4206" not in arts


def test_rows_to_queue_accepts_hj_skus() -> None:
    rows = extract_jouef_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows, min_price_eur=120)
    assert {e.article.value for e in q.entries} >= {
        "HJ2461",
        "HJ2461S",
        "HJ2342",
        "HJ2471",
        "HJ2471S",
    }
    assert all(e.price_eur is None for e in q.entries)


def test_article_number_digits_unchanged() -> None:
    assert ArticleNumber.parse("21002").value == "21002"
    assert ArticleNumber.parse("hj2461").value == "HJ2461"
    assert ArticleNumber.parse("HJ2461S").value == "HJ2461S"
    with pytest.raises(ValueError):
        ArticleNumber.parse("HJ4206HM")
    with pytest.raises(ValueError):
        ArticleNumber.parse("abc")


def test_jouef_shop_site_stub_raises() -> None:
    site = shop_site_for("jouef")
    assert isinstance(site, JouefShopSite)
    with pytest.raises(JouefShopNotImplementedError):
        site.search_url("HJ2461")
    with pytest.raises(JouefShopNotImplementedError):
        parse_jouef_pdp("<html></html>", canonical_url="https://fr.jouef.com/x", article="HJ2461")
