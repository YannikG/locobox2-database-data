from __future__ import annotations

from locobox_cli.application.queue.approve import ApproveQueue
from locobox_cli.application.queue.diff import DiffQueueAgainstRepo
from locobox_cli.application.queue.parse import parse_queue_text
from locobox_cli.domain.manufacturer import Manufacturer


class FakeRepo:
    def __init__(self, numbers: set[str]) -> None:
        self._numbers = numbers

    def list_article_numbers(self, manufacturer: Manufacturer) -> set[str]:
        return set(self._numbers)

    def exists(self, manufacturer: Manufacturer, article_number: str) -> bool:
        return article_number in self._numbers


def test_diff_missing_and_existing() -> None:
    queue = parse_queue_text("10001\n10002\n10003\n")
    diff = DiffQueueAgainstRepo(FakeRepo({"10002"})).run(Manufacturer.PIKO, queue)
    assert diff.missing == ("10001", "10003")
    assert diff.existing == ("10002",)


def test_approve_only_missing_and_min_price() -> None:
    cand = parse_queue_text(
        "10001\tLok\tlocomotive\t200 EUR\n"
        "10002\tLok\tlocomotive\t50 EUR\n"
        "10003\tLok\tlocomotive\t180 EUR\n"
    )
    approved = ApproveQueue(repo=FakeRepo({"10001"})).run(
        cand,
        manufacturer=Manufacturer.PIKO,
        only_missing=True,
        min_price_eur=100,
    )
    assert [e.article.value for e in approved.entries] == ["10003"]


def test_approve_include_exclude() -> None:
    cand = parse_queue_text("10001\n10002\n10003\n")
    approved = ApproveQueue().run(
        cand,
        include={"10001", "10003"},
        exclude={"10003"},
    )
    assert [e.article.value for e in approved.entries] == ["10001"]
