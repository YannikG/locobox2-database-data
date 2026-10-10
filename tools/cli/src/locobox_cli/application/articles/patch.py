from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from locobox_cli.application.articles.allowed_paths import assert_allowed_set_path
from locobox_cli.application.articles.validate import ValidateArticle
from locobox_cli.domain.json_path import get_path, set_path


@dataclass(frozen=True, slots=True)
class PatchResult:
    before: Any
    after: Any
    path: str
    article: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SetField:
    validator: ValidateArticle

    def run(self, article: dict[str, Any], path: str, value: Any) -> PatchResult:
        assert_allowed_set_path(path)
        data = deepcopy(article)
        before = get_path(data, path)
        set_path(data, path, value)
        data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.validator.assert_valid(data)
        return PatchResult(before=before, after=value, path=path, article=data)


@dataclass(frozen=True, slots=True)
class PatchArticle:
    """Apply one or more set operations; validate once at the end."""

    validator: ValidateArticle

    def run(self, article: dict[str, Any], changes: list[tuple[str, Any]]) -> tuple[dict[str, Any], list[PatchResult]]:
        data = deepcopy(article)
        results: list[PatchResult] = []
        for path, value in changes:
            assert_allowed_set_path(path)
            before = get_path(data, path)
            set_path(data, path, value)
            results.append(PatchResult(before=before, after=value, path=path, article=data))
        data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.validator.assert_valid(data)
        return data, results


def parse_value_arg(raw: str, *, as_json: bool) -> Any:
    if as_json:
        return json.loads(raw)
    if raw == "null":
        return None
    return raw


def append_audit_log(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_patch_jsonl(path: Path) -> list[tuple[str, str, Any]]:
    """
    Each line: {"article":"21002","mfr":"piko","path":"model.type","value":"BR 187"}
    or {"file":"articles/piko/21002.json","path":"...","value":...}
    """
    rows: list[tuple[str, str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        obj = json.loads(s)
        if "path" not in obj or "value" not in obj:
            raise ValueError(f"{path}:{line_no}: need path and value")
        key = obj.get("file") or f"{obj.get('mfr')}:{obj.get('article')}"
        if not key or key == "None:None":
            raise ValueError(f"{path}:{line_no}: need file or mfr+article")
        rows.append((str(key), str(obj["path"]), obj["value"]))
    return rows
