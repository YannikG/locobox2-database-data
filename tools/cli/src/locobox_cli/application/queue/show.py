from __future__ import annotations

from locobox_cli.domain.queue import QueueDocument


def format_queue_show(document: QueueDocument, *, limit: int | None = None) -> str:
    lines: list[str] = [
        f"entries: {len(document.entries)}",
    ]
    if document.header_comments:
        lines.append("headers:")
        lines.extend(f"  {h}" for h in document.header_comments)
    lines.append("articles:")
    entries = document.entries
    if limit is not None:
        entries = entries[:limit]
    for entry in entries:
        bits = [entry.article.value]
        if entry.kind:
            bits.append(entry.kind)
        if entry.section:
            bits.append(entry.section)
        if entry.price_eur is not None:
            bits.append(f"{entry.price_eur:g} EUR")
        if entry.note:
            bits.append(f"# {entry.note}")
        lines.append("  " + " | ".join(bits))
    if limit is not None and len(document.entries) > limit:
        lines.append(f"  … {len(document.entries) - limit} more")
    return "\n".join(lines) + "\n"
