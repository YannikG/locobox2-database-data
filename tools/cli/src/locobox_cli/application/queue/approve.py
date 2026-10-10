from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from locobox_cli.application.ports.article_repo import ArticleRepository
from locobox_cli.domain.manufacturer import Manufacturer
from locobox_cli.domain.queue import QueueDocument, QueueEntry


@dataclass(frozen=True, slots=True)
class ApproveQueue:
    """Build an approved queue from candidates with optional filters."""

    repo: Optional[ArticleRepository] = None

    def run(
        self,
        candidates: QueueDocument,
        *,
        manufacturer: Optional[Manufacturer] = None,
        only_missing: bool = False,
        min_price_eur: Optional[float] = None,
        include: Optional[set[str]] = None,
        exclude: Optional[set[str]] = None,
    ) -> QueueDocument:
        present: set[str] = set()
        if only_missing:
            if self.repo is None or manufacturer is None:
                raise ValueError("only_missing requires article repository and manufacturer")
            present = self.repo.list_article_numbers(manufacturer)

        approved: list[QueueEntry] = []
        for entry in candidates.entries:
            n = entry.article.value
            if include is not None and n not in include:
                continue
            if exclude is not None and n in exclude:
                continue
            if min_price_eur is not None:
                if entry.price_eur is None or entry.price_eur <= min_price_eur:
                    continue
            if only_missing and n in present:
                continue
            approved.append(entry)

        headers = list(candidates.header_comments)
        headers.append(f"# approved: {len(approved)} of {len(candidates.entries)} candidates")
        return QueueDocument(entries=approved, header_comments=headers)
