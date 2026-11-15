from __future__ import annotations

import re
from dataclasses import dataclass

# Digits (PIKO/Roco/Trix) or Lima Expert / Hobby SKUs (HL#### / HC####).
_ARTICLE_RE = re.compile(r"^(?:\d{4,8}|H[LC]\d{3,5})$", re.I)
_LIMA_SKU_RE = re.compile(r"^(H[LC])\s*(\d{3,5})$", re.I)


@dataclass(frozen=True, slots=True)
class ArticleNumber:
    """Canonical shop/catalog article number (digits or Lima HL/HC prefix)."""

    value: str

    def __post_init__(self) -> None:
        if not _ARTICLE_RE.fullmatch(self.value):
            raise ValueError(f"invalid article number: {self.value!r}")

    @classmethod
    def parse(cls, raw: str) -> ArticleNumber:
        s = raw.strip()
        if not s or s.startswith("#"):
            raise ValueError(f"not an article number: {raw!r}")
        lima = _LIMA_SKU_RE.fullmatch(s)
        if lima:
            return cls(f"{lima.group(1).upper()}{lima.group(2)}")
        if not s.isdigit():
            raise ValueError(f"article number must be digits or Lima HL/HC SKU: {raw!r}")
        return cls(s)

    def __str__(self) -> str:
        return self.value
