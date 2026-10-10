from __future__ import annotations

from typing import Protocol

from locobox_cli.domain.manufacturer import Manufacturer


class ArticleRepository(Protocol):
    def list_article_numbers(self, manufacturer: Manufacturer) -> set[str]:
        """Return article numbers present under articles/{slug}/."""

    def exists(self, manufacturer: Manufacturer, article_number: str) -> bool:
        ...
