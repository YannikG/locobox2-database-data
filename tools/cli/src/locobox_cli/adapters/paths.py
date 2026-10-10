from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up until articles/ and contracts/ are siblings (locobox data repo)."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / "articles").is_dir() and (candidate / "contracts").is_dir():
            return candidate
    raise FileNotFoundError(
        "repo root not found (expected directories articles/ and contracts/). "
        "Run from the locobox2-database-data repository."
    )
