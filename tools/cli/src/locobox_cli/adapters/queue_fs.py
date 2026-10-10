from __future__ import annotations

import shutil
from pathlib import Path

from locobox_cli.application.ports.queue_store import QueueKind
from locobox_cli.application.queue.parse import parse_queue_text, render_queue_text
from locobox_cli.domain.queue import QueueDocument


class FilesystemQueueStore:
    """Campaign working state under ``.tmp/import/{campaign}/``."""

    def __init__(self, repo_root: Path) -> None:
        self._root = repo_root.resolve()
        self._base = self._root / ".tmp" / "import"

    def campaign_dir(self, campaign: str) -> Path:
        safe = campaign.strip().replace("/", "-").replace("..", ".")
        if not safe:
            raise ValueError("campaign name must not be empty")
        return self._base / safe

    def path_for(self, campaign: str, kind: QueueKind) -> Path:
        return self.campaign_dir(campaign) / f"{kind.value}.txt"

    def load(self, campaign: str, kind: QueueKind) -> QueueDocument:
        path = self.path_for(campaign, kind)
        if not path.is_file():
            raise FileNotFoundError(f"queue file missing: {path}")
        return parse_queue_text(path.read_text(encoding="utf-8"))

    def save(self, campaign: str, kind: QueueKind, document: QueueDocument) -> Path:
        path = self.path_for(campaign, kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_queue_text(document, numbers_only=False), encoding="utf-8")
        return path

    def clear(
        self,
        campaign: str,
        *,
        candidates: bool,
        approved: bool,
        html_cache: bool,
        dry_run: bool,
    ) -> list[Path]:
        camp = self.campaign_dir(campaign)
        targets: list[Path] = []
        if candidates:
            targets.append(camp / "candidates.txt")
        if approved:
            targets.append(camp / "approved.txt")
        if html_cache:
            targets.append(camp / "html")
        # also clear common sidecar reports
        if candidates or approved:
            for name in ("diff-missing.txt", "diff-existing.txt", "blocked.txt"):
                targets.append(camp / name)

        removed: list[Path] = []
        for path in targets:
            if not path.exists():
                continue
            removed.append(path)
            if dry_run:
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        return removed
