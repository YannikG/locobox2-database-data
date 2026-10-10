from __future__ import annotations

import re
from dataclasses import dataclass

_ARTICLE_RE = re.compile(r"^\d{4,8}$")


@dataclass(frozen=True, slots=True)
class ArticleNumber:
    """Canonical shop/catalog article number (digits only)."""

    value: str

    def __post_init__(self) -> None:
        if not _ARTICLE_RE.fullmatch(self.value):
            raise ValueError(f"invalid article number: {self.value!r}")

    @classmethod
    def parse(cls, raw: str) -> ArticleNumber:
        s = raw.strip()
        if not s or s.startswith("#"):
            raise ValueError(f"not an article number: {raw!r}")
        # allow leading zeros stripped only if still 4–8 digits after strip of spaces
        if not s.isdigit():
            raise ValueError(f"article number must be digits: {raw!r}")
        return cls(s)

    def __str__(self) -> str:
        return self.value
