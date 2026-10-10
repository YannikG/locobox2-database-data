from __future__ import annotations

from dataclasses import dataclass

from locobox_cli.application.queue.parse import parse_queue_text, render_queue_text
from locobox_cli.domain.queue import QueueDocument


@dataclass(frozen=True, slots=True)
class NormalizeQueue:
    """Deduplicate and canonicalize a queue text file."""

    numbers_only: bool = True

    def run(self, text: str) -> tuple[QueueDocument, str]:
        doc = parse_queue_text(text)
        rendered = render_queue_text(doc, numbers_only=self.numbers_only)
        return doc, rendered
