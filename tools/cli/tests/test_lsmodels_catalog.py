from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.lsmodels.catalog import (
    extract_lsmodels_catalog_rows,
    rows_to_queue,
)

FIXTURE = Path(__file__).parent / "fixtures" / "lsmodels_catalog_snippet.txt"


def test_extract_locomotives_skips_sound_mw_and_wagons() -> None:
    rows = extract_lsmodels_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "16075" in arts
    assert "16575" in arts
    assert "16100" in arts
    assert "16600" in arts
    # Sound suffix S skipped (ArticleNumber digits only)
    assert "16075S" not in arts
    assert "16575S" not in arts
    # Personenwagen / MW skipped with locomotives_only
    assert "17201" not in arts
    assert "17202" not in arts
    assert all(r.price_eur is None for r in rows)


def test_extract_all_rolling_stock_keeps_wagons_not_sound() -> None:
    rows = extract_lsmodels_catalog_rows(
        FIXTURE.read_text(encoding="utf-8"),
        locomotives_only=False,
    )
    arts = [r.article for r in rows]
    assert "16075" in arts
    assert "17201" in arts
    assert "17202" in arts
    assert "16075S" not in arts


def test_rows_to_queue_keeps_unknown_price_with_min_filter() -> None:
    rows = extract_lsmodels_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows, min_price_eur=120)
    assert len(q.entries) == len(rows)
