from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from locobox_cli.domain.manufacturer import Manufacturer


class FilesystemArticleRepository:
    def __init__(self, repo_root: Path) -> None:
        self._root = repo_root.resolve()
        self._articles = self._root / "articles"

    def manufacturer_dir(self, manufacturer: Manufacturer) -> Path:
        return self._articles / manufacturer.slug

    def article_path(self, manufacturer: Manufacturer, article_number: str) -> Path:
        return self.manufacturer_dir(manufacturer) / f"{article_number}.json"

    def list_article_numbers(self, manufacturer: Manufacturer) -> set[str]:
        d = self.manufacturer_dir(manufacturer)
        if not d.is_dir():
            return set()
        return {p.stem for p in d.glob("*.json") if p.is_file()}

    def exists(self, manufacturer: Manufacturer, article_number: str) -> bool:
        return self.article_path(manufacturer, article_number).is_file()

    def load(self, manufacturer: Manufacturer, article_number: str) -> dict[str, Any]:
        path = self.article_path(manufacturer, article_number)
        return json.loads(path.read_text(encoding="utf-8"))

    def load_path(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def save_path(self, path: Path, article: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(article, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def save(self, manufacturer: Manufacturer, article_number: str, article: dict[str, Any]) -> Path:
        path = self.article_path(manufacturer, article_number)
        self.save_path(path, article)
        return path

    def resolve_article_file(
        self,
        *,
        path: Path | None = None,
        manufacturer: Manufacturer | None = None,
        article_number: str | None = None,
    ) -> Path:
        if path is not None:
            return path.resolve()
        if manufacturer is None or not article_number:
            raise ValueError("need --file or --mfr and --article")
        return self.article_path(manufacturer, article_number)
