from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.lima.catalog import (
    extract_lima_catalog_rows,
    rows_to_queue,
)
from locobox_cli.domain.article import ArticleNumber

FIXTURE = Path(__file__).parent / "fixtures" / "lima_catalog_snippet.txt"


def test_article_number_accepts_lima_skus() -> None:
    assert ArticleNumber.parse("HL2664").value == "HL2664"
    assert ArticleNumber.parse("hl 2664").value == "HL2664"
    assert ArticleNumber.parse("HC5000").value == "HC5000"
    assert ArticleNumber.parse("21002").value == "21002"
    try:
        ArticleNumber.parse("XX1234")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_extract_locomotives_skips_sets_and_hobby() -> None:
    rows = extract_lima_catalog_rows(FIXTURE.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "HL2664" in arts
    assert "HL2665" in arts
    assert "HL2666" in arts  # automotrice diesel
    assert "HL2673" in arts  # spaced HL 2673
    assert "HL1682" not in arts  # ETR set base
    assert "HL5050" not in arts  # carrozze set
    assert "HC5000" not in arts  # Hobby wagon
    by_art = {r.article: r for r in rows}
    assert by_art["HL2664"].price_eur == 173.9
    assert by_art["HL2664"].kind == "Elektrolok"
    assert by_art["HL2666"].kind == "Diesellok"


def test_rows_to_queue_min_price_and_all_rolling_stock() -> None:
    rows = extract_lima_catalog_rows(
        FIXTURE.read_text(encoding="utf-8"), locomotives_only=False
    )
    arts = {r.article for r in rows}
    assert "HL1682" in arts
    assert "HC5000" in arts
    q = rows_to_queue(
        extract_lima_catalog_rows(FIXTURE.read_text(encoding="utf-8")),
        min_price_eur=150,
    )
    assert all(e.price_eur is None or e.price_eur > 150 for e in q.entries)
    assert {e.article.value for e in q.entries} >= {"HL2664", "HL2673"}
