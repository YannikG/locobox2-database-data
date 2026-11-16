from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.bemo.catalog import (
    extract_bemo_catalog_rows,
    rows_to_queue,
)

FIXTURE = Path(__file__).parent / "fixtures" / "bemo_catalog_snippet.txt"


def test_extract_locomotives_normalizes_spaced_skus() -> None:
    rows = extract_bemo_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "1258168" in arts
    assert "1358168" in arts
    assert "1010201" in arts
    assert "1255100" in arts
    assert "2281115" in arts
    assert "2250100" not in arts
    assert "3245101" not in arts


def test_extract_all_rolling_stock_includes_wagons() -> None:
    rows = extract_bemo_catalog_rows(
        FIXTURE.read_text(encoding="utf-8"), locomotives_only=False
    )
    arts = {r.article for r in rows}
    assert "2250100" in arts
    assert "3245101" in arts
    assert "1258168" in arts


def test_rows_to_queue() -> None:
    rows = extract_bemo_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows)
    assert q.entries
    assert all(e.article.value.isdigit() for e in q.entries)
    assert any(e.kind in {"Elektrolok", "Dampflok", "Diesellok", "Triebwagen", "Zahnradlok", "Rangierlok", "Lokomotive"} for e in q.entries)
