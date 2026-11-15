from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.trix.catalog import (
    extract_trix_catalog_rows,
    rows_to_queue,
)

FIXTURE = Path(__file__).parent / "fixtures" / "trix_h0_nh2026_catalog_snippet.txt"


def test_extract_locomotives_skips_triebwagen_and_wagons() -> None:
    rows = extract_trix_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "25061" in arts
    assert "25477" in arts
    assert "25492" in arts  # Schlepptender-Dampflokomotive
    # Index-only / non-loco titles stay out when locomotives_only
    assert "25852" not in arts
    assert "22482" not in arts
    assert "23234" not in arts
    by_art = {r.article: r for r in rows}
    assert by_art["25061"].price_eur == 699.0
    assert by_art["25492"].price_eur == 599.0
    assert by_art["25477"].kind == "Dampflok"


def test_rows_to_queue_min_price_filter() -> None:
    rows = extract_trix_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    q = rows_to_queue(rows, min_price_eur=120)
    assert all(e.price_eur is None or e.price_eur > 120 for e in q.entries)
    assert {e.article.value for e in q.entries} >= {"25061", "25477", "25492"}
