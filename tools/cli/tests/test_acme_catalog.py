from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.acme.catalog import (
    extract_acme_catalog_rows,
    rows_to_queue,
)
from locobox_cli.adapters.sources.acme.shop_site import AcmeFlyerSite
from locobox_cli.adapters.sources.shop_site import shop_site_for
from locobox_cli.domain.manufacturer import Manufacturer

FIXTURE = Path(__file__).parent / "fixtures" / "acme_flyer_catalog_snippet.txt"


def test_manufacturer_acme_parse_and_display() -> None:
    mfr = Manufacturer.parse("acme")
    assert mfr is Manufacturer.ACME
    assert mfr.display_name == "ACME"
    assert mfr.slug == "acme"


def test_extract_locomotives_from_flyer_skips_sets_and_cars() -> None:
    rows = extract_acme_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "60655" in arts
    assert "69655" in arts
    assert "60654" in arts
    assert "69654" in arts
    # Wagon / set / exclusive codes stay out when locomotives_only
    assert "70140" not in arts
    assert "51220" not in arts
    assert "90229" not in arts
    assert "90267" not in arts
    assert "20132" not in arts  # Milano ZIP on flyer footer
    by_art = {r.article: r for r in rows}
    assert by_art["60655"].price_eur == 212.0
    assert by_art["60654"].price_eur == 212.0
    assert by_art["60655"].kind == "Elektrolok"


def test_ac_prefixed_sku_normalizes_to_digits() -> None:
    text = "Locomotiva elettrica\nAC60655                        199\nLokomotive Re 450\n"
    rows = extract_acme_catalog_rows(text)
    assert [r.article for r in rows] == ["60655"]
    assert rows[0].price_eur == 199.0


def test_rows_to_queue_min_price_filter() -> None:
    rows = extract_acme_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows, min_price_eur=200)
    assert all(e.price_eur is None or e.price_eur > 200 for e in q.entries)
    assert {e.article.value for e in q.entries} >= {"60655", "60654", "69655", "69654"}


def test_shop_site_flyer_url() -> None:
    site = shop_site_for("acme")
    assert isinstance(site, AcmeFlyerSite)
    assert site.fallback_pdp_url("60655") == "https://www.acmetreni.it/files/AC60655.pdf"
    assert site.is_pdp_url("https://www.acmetreni.it/files/AC60655.pdf", "60655")
    assert not site.is_pdp_url("https://www.acmetreni.it/files/AC60654.pdf", "60655")


def test_herbst_sku_before_title_still_extracts_locos() -> None:
    text = (
        Path(__file__).parent / "fixtures" / "acme_herbst_sku_before_title.txt"
    ).read_text(encoding="utf-8")
    rows = extract_acme_catalog_rows(text)
    arts = {r.article for r in rows}
    assert arts == {"60741", "69741", "60197", "69197"}
    by_art = {r.article: r for r in rows}
    assert by_art["60741"].price_eur == 217.0
    assert by_art["69741"].price_eur == 217.0
    assert by_art["60197"].price_eur == 197.0
    assert "55390" not in arts
