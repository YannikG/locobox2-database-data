from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.roco.catalog import (
    extract_roco_catalog_rows,
    rows_to_queue,
)

FIXTURE = Path(__file__).parent / "fixtures" / "roco_tt_catalog_snippet.txt"


def test_extract_locomotives_skips_triebwagen_and_wagons() -> None:
    rows = extract_roco_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "7180020" in arts
    assert "7190020" in arts
    assert "7580046" in arts
    assert "7380031" in arts
    assert "7380039" in arts  # collector edition loco
    assert "7780011" not in arts
    assert "7790012" not in arts
    assert "6280074" not in arts
    assert all(r.price_eur is None for r in rows)


def test_rows_to_queue_keeps_unknown_price_with_min_filter() -> None:
    rows = extract_roco_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows, min_price_eur=120)
    assert len(q.entries) == len(rows)
