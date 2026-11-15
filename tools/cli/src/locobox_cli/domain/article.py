from __future__ import annotations

import re
from dataclasses import dataclass

# Classic PIKO / Roco / Trix numeric SKUs.
_NUMERIC_RE = re.compile(r"^\d{4,8}$")
# REE-style: MB-263S, TGV-004SAC, JM-001 (canonical after normalize).
_CANON_ALPHANUM_RE = re.compile(r"^[A-Z]{1,6}-\d{1,6}[A-Z]{0,6}$")
# Accept shop/catalog variants: "MB 176S", "MB263S", "TGV-004 S", "mb-263sac".
_ALPHANUM_PARSE_RE = re.compile(
    r"^([A-Za-z]{1,6})[-\s]*(\d{1,6})[-\s]*([A-Za-z]{0,6})$"
)
# Match an article token at the start of a free-form queue line (may contain spaces).
QUEUE_ARTICLE_AT_START = re.compile(
    r"^(?P<article>"
    r"\d{4,8}"
    r"|"
    r"[A-Za-z]{1,6}(?:[-\s]*\d{1,6})(?:[-\s]*[A-Za-z]+)?"
    r")"
)


def _normalize_alphanum(raw: str) -> str:
    s = raw.strip().upper()
    m = _ALPHANUM_PARSE_RE.fullmatch(s)
    if not m:
        raise ValueError(f"invalid article number: {raw!r}")
    prefix, digits, suffix = m.group(1), m.group(2), m.group(3)
    return f"{prefix}-{digits}{suffix}"


@dataclass(frozen=True, slots=True)
class ArticleNumber:
    """Canonical shop/catalog article number (numeric or REE-style alphanumeric)."""

    value: str

    def __post_init__(self) -> None:
        if _NUMERIC_RE.fullmatch(self.value):
            return
        if _CANON_ALPHANUM_RE.fullmatch(self.value):
            return
        raise ValueError(f"invalid article number: {self.value!r}")

    @classmethod
    def parse(cls, raw: str) -> ArticleNumber:
        s = raw.strip()
        if not s or s.startswith("#"):
            raise ValueError(f"not an article number: {raw!r}")
        if s.isdigit():
            if not _NUMERIC_RE.fullmatch(s):
                raise ValueError(f"invalid article number: {raw!r}")
            return cls(s)
        return cls(_normalize_alphanum(s))

    def compact(self) -> str:
        """Shop-style SKU without hyphens (e.g. MB263S)."""
        return self.value.replace("-", "")

    def __str__(self) -> str:
        return self.value
