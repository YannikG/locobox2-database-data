from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.ree.catalog import extract_ree_catalog_rows, rows_to_queue

FIXTURE = Path(__file__).parent / "fixtures" / "ree_catalog_snippet.txt"


def test_extract_motorized_normalizes_refs() -> None:
    rows = extract_ree_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "MB-263" in arts
    assert "MB-263S" in arts
    assert "MB-263SAC" in arts
    assert "MB-176S" in arts
    assert "TGV-004" in arts
    assert "TGV-004S" in arts
    assert "TGV-005S" in arts
    assert "JM-001" in arts
    assert "WB-860" not in arts
    assert "VB-489" not in arts


def test_extract_all_rolling_stock_includes_wagons() -> None:
    rows = extract_ree_catalog_rows(
        FIXTURE.read_text(encoding="utf-8"), locomotives_only=False
    )
    arts = {r.article for r in rows}
    assert "WB-860" in arts
    assert "VB-489" in arts


def test_rows_to_queue() -> None:
    rows = extract_ree_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows)
    assert q.entries
    assert all(e.article.value.startswith(("MB-", "TGV-", "JM-")) for e in q.entries)
