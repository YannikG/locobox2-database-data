from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.queue_fs import FilesystemQueueStore
from locobox_cli.application.ports.queue_store import QueueKind
from locobox_cli.application.queue.clear import ClearQueueWorkingState
from locobox_cli.application.queue.parse import parse_queue_text


def test_clear_dry_run_and_apply(tmp_path: Path) -> None:
    # minimal fake repo root
    (tmp_path / "articles").mkdir()
    (tmp_path / "contracts").mkdir()
    store = FilesystemQueueStore(tmp_path)
    doc = parse_queue_text("10001\n10002\n")
    store.save("demo", QueueKind.CANDIDATES, doc)
    store.save("demo", QueueKind.APPROVED, doc)
    html = store.campaign_dir("demo") / "html"
    html.mkdir(parents=True)
    (html / "10001.html").write_text("<html></html>", encoding="utf-8")

    would = ClearQueueWorkingState(store).run(
        "demo",
        candidates=True,
        approved=True,
        html_cache=True,
        dry_run=True,
    )
    assert store.path_for("demo", QueueKind.CANDIDATES).is_file()
    assert any(p.name == "candidates.txt" for p in would)

    ClearQueueWorkingState(store).run(
        "demo",
        candidates=True,
        approved=True,
        html_cache=True,
        dry_run=False,
    )
    assert not store.path_for("demo", QueueKind.CANDIDATES).exists()
    assert not store.path_for("demo", QueueKind.APPROVED).exists()
    assert not html.exists()
