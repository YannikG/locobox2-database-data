from __future__ import annotations

from dataclasses import dataclass

from locobox_cli.application.ports.article_repo import ArticleRepository
from locobox_cli.domain.manufacturer import Manufacturer
from locobox_cli.domain.queue import QueueDiff, QueueDocument


@dataclass(frozen=True, slots=True)
class DiffQueueAgainstRepo:
    repo: ArticleRepository

    def run(self, manufacturer: Manufacturer, queue: QueueDocument) -> QueueDiff:
        present = self.repo.list_article_numbers(manufacturer)
        missing: list[str] = []
        existing: list[str] = []
        for entry in queue.entries:
            n = entry.article.value
            if n in present:
                existing.append(n)
            else:
                missing.append(n)
        return QueueDiff(
            missing=tuple(missing),
            existing=tuple(existing),
            queue_size=len(queue.entries),
            repo_size=len(present),
        )
