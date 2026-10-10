from __future__ import annotations

from locobox_cli.application.queue.normalize import NormalizeQueue
from locobox_cli.application.queue.parse import parse_queue_text, render_queue_text


def test_parse_dedupes_and_keeps_meta() -> None:
    text = """# header
21002\tElektrolok\tlocomotive\t129,99 EUR
21002
71005  # note
# skip trailing
"""
    doc = parse_queue_text(text)
    assert [e.article.value for e in doc.entries] == ["21002", "71005"]
    assert doc.entries[0].kind == "Elektrolok"
    assert doc.entries[0].price_eur == 129.99
    assert doc.entries[1].note == "note"
    assert doc.header_comments[0] == "# header"


def test_normalize_numbers_only() -> None:
    text = "71005\n21002\n71005\n"
    doc, rendered = NormalizeQueue(numbers_only=True).run(text)
    assert [e.article.value for e in doc.entries] == ["71005", "21002"]
    assert rendered == "71005\n21002\n"


def test_render_roundtrip_numbers() -> None:
    doc = parse_queue_text("10001\n10002\n")
    assert parse_queue_text(render_queue_text(doc, numbers_only=True)).as_number_set() == {
        "10001",
        "10002",
    }
