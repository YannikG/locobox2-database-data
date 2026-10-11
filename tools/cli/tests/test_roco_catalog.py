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


WINTER = Path(__file__).parent / "fixtures" / "roco_winter_2018_catalog_snippet.txt"


def test_extract_art_nr_winter_catalog_locomotives() -> None:
    rows = extract_roco_catalog_rows(WINTER.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "72016" in arts
    assert "78016" in arts
    assert "72254" in arts
    assert "73256" in arts  # 421 SBB despite prose on title line
    assert "73224" in arts  # BR 170; wrapped Doppelstockwagen must not kill loco state
    assert "74160" not in arts
    assert "64188" not in arts
    by_art = {r.article: r for r in rows}
    assert "421" in by_art["73256"].line_context
    assert "BR 170" in by_art["73224"].line_context


H0E = Path(__file__).parent / "fixtures" / "roco_h0e_2019_catalog_snippet.txt"


def test_extract_h0e_decoder_frac_skus() -> None:
    rows = extract_roco_catalog_rows(H0E.read_text(encoding="utf-8"))
    arts = [r.article for r in rows]
    assert "33298" in arts
    assert "33299" in arts
    assert "33300" in arts
    assert "33301" in arts
    assert "33272" in arts
    assert "33273" in arts
    assert "33253" in arts
    assert "33204" in arts  # second SKU on dual loco page
    assert "33238" in arts
    assert "34031" not in arts
    assert "34030" not in arts
    assert "34060" not in arts
