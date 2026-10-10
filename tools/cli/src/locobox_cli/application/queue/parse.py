from __future__ import annotations

import re
from typing import Optional

from locobox_cli.domain.article import ArticleNumber
from locobox_cli.domain.queue import QueueDocument, QueueEntry

# Formats:
#   21002
#   21002\tElektrolok\tlocomotive\t129,99 EUR\t…
#   21002  # comment
_META_PRICE = re.compile(
    r"(?P<price>\d+(?:[.,]\d+)?)\s*(?:EUR|€)?",
    re.I,
)


def _parse_price(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    s = raw.strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_queue_line(line: str) -> tuple[Optional[QueueEntry], Optional[str]]:
    """
    Parse one queue line.

    Returns (entry, header_comment). Exactly one of them is set for meaningful lines;
    blank lines yield (None, None).
    """
    stripped = line.strip()
    if not stripped:
        return None, None
    if stripped.startswith("#"):
        return None, stripped

    # split inline comment
    if "#" in stripped:
        main, _, comment = stripped.partition("#")
        note = comment.strip() or None
        stripped = main.strip()
    else:
        note = None

    if "\t" in stripped:
        parts = [p.strip() for p in stripped.split("\t")]
    else:
        parts = stripped.split()

    if not parts:
        return None, None

    article = ArticleNumber.parse(parts[0])
    kind = parts[1] if len(parts) > 1 else None
    section = parts[2] if len(parts) > 2 else None
    price_eur: Optional[float] = None
    if len(parts) > 3:
        price_eur = _parse_price(parts[3])
        if price_eur is None:
            m = _META_PRICE.search(parts[3])
            if m:
                price_eur = _parse_price(m.group("price"))

    return (
        QueueEntry(
            article=article,
            kind=kind,
            section=section,
            price_eur=price_eur,
            note=note,
            raw_line=line.rstrip("\n"),
        ),
        None,
    )


def parse_queue_text(text: str) -> QueueDocument:
    headers: list[str] = []
    entries: list[QueueEntry] = []
    seen: set[str] = set()
    for line in text.splitlines():
        entry, header = parse_queue_line(line)
        if header is not None:
            headers.append(header)
            continue
        if entry is None:
            continue
        if entry.article.value in seen:
            continue
        seen.add(entry.article.value)
        entries.append(entry)
    return QueueDocument(entries=entries, header_comments=headers)


def render_queue_text(document: QueueDocument, *, numbers_only: bool = False) -> str:
    lines: list[str] = []
    lines.extend(document.header_comments)
    if document.header_comments and not document.header_comments[-1].startswith("#"):
        pass
    for entry in document.entries:
        if numbers_only:
            lines.append(entry.article.value)
            continue
        if entry.kind or entry.section or entry.price_eur is not None:
            price = ""
            if entry.price_eur is not None:
                price = f"{entry.price_eur:g} EUR"
            cols = [
                entry.article.value,
                entry.kind or "",
                entry.section or "",
                price,
            ]
            line = "\t".join(cols).rstrip("\t")
        else:
            line = entry.article.value
        if entry.note:
            line = f"{line}  # {entry.note}"
        lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")
