from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.maerklin.catalog import (
    extract_maerklin_catalog_rows,
    rows_to_queue,
)

FIXTURE = Path(__file__).parent / "fixtures" / "maerklin_h0_nh2026_catalog_snippet.txt"


def test_extract_locomotives_skips_triebwagen_and_wagons() -> None:
    rows = extract_maerklin_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "39661" in arts
    assert "38477" in arts
    assert "30391" in arts  # Rheingold-Elektrolokomotive
    assert "39852" not in arts
    assert "42491" not in arts
    by_art = {r.article: r for r in rows}
    assert by_art["39661"].price_eur == 699.0
    assert by_art["38477"].price_eur == 599.0
    assert by_art["30391"].kind == "Elektrolok"
    assert by_art["38477"].kind == "Dampflok"


def test_rows_to_queue_min_price_filter() -> None:
    rows = extract_maerklin_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows, min_price_eur=120)
    assert all(e.price_eur is None or e.price_eur > 120 for e in q.entries)
    assert {e.article.value for e in q.entries} >= {"39661", "38477", "30391"}
