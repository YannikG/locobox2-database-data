from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Protocol

from locobox_cli.domain.queue import QueueDocument


class QueueKind(str, Enum):
    CANDIDATES = "candidates"
    APPROVED = "approved"


class QueueStore(Protocol):
    def campaign_dir(self, campaign: str) -> Path:
        ...

    def path_for(self, campaign: str, kind: QueueKind) -> Path:
        ...

    def load(self, campaign: str, kind: QueueKind) -> QueueDocument:
        ...

    def save(self, campaign: str, kind: QueueKind, document: QueueDocument) -> Path:
        ...

    def clear(
        self,
        campaign: str,
        *,
        candidates: bool,
        approved: bool,
        html_cache: bool,
        dry_run: bool,
    ) -> list[Path]:
        """Delete selected working-state paths. Returns paths that were (or would be) removed."""
