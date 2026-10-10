from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from locobox_cli.application.ports.queue_store import QueueStore


@dataclass(frozen=True, slots=True)
class ClearQueueWorkingState:
    store: QueueStore

    def run(
        self,
        campaign: str,
        *,
        candidates: bool = True,
        approved: bool = True,
        html_cache: bool = False,
        dry_run: bool = False,
    ) -> list[Path]:
        return self.store.clear(
            campaign,
            candidates=candidates,
            approved=approved,
            html_cache=html_cache,
            dry_run=dry_run,
        )
