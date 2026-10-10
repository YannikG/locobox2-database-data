from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.piko.catalog import extract_piko_catalog_rows, rows_to_queue

FIXTURE = Path(__file__).parent / "fixtures" / "piko_catalog_snippet.txt"


def test_extract_skips_digital_and_keeps_rolling_stock() -> None:
    rows = extract_piko_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "21002" in arts
    assert "52880" in arts
    assert "55412" not in arts


def test_rows_to_queue_min_price() -> None:
    rows = extract_piko_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows, min_price_eur=200)
    assert [e.article.value for e in q.entries] == ["21002"]
