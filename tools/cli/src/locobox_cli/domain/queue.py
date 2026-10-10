from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from locobox_cli.domain.article import ArticleNumber


@dataclass(frozen=True, slots=True)
class QueueEntry:
    article: ArticleNumber
    kind: Optional[str] = None
    section: Optional[str] = None
    price_eur: Optional[float] = None
    note: Optional[str] = None
    raw_line: Optional[str] = None


@dataclass(slots=True)
class QueueDocument:
    """Ordered unique article queue with optional header comments."""

    entries: list[QueueEntry] = field(default_factory=list)
    header_comments: list[str] = field(default_factory=list)

    def article_numbers(self) -> list[ArticleNumber]:
        return [e.article for e in self.entries]

    def as_number_set(self) -> set[str]:
        return {e.article.value for e in self.entries}


@dataclass(frozen=True, slots=True)
class QueueDiff:
    missing: tuple[str, ...]
    existing: tuple[str, ...]
    queue_size: int
    repo_size: int
