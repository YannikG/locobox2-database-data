from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    message: str
    path: str


@dataclass(frozen=True, slots=True)
class ValidateArticle:
    schema: dict[str, Any]

    @classmethod
    def from_contracts(cls, repo_root: Path) -> ValidateArticle:
        schema_path = repo_root / "contracts" / "article.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        return cls(schema=schema)

    def run(self, article: dict[str, Any]) -> list[ValidationIssue]:
        validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        issues: list[ValidationIssue] = []
        for err in sorted(validator.iter_errors(article), key=lambda e: list(e.absolute_path)):
            path = ".".join(str(p) for p in err.absolute_path) or "(root)"
            issues.append(ValidationIssue(message=err.message, path=path))
        return issues

    def assert_valid(self, article: dict[str, Any]) -> None:
        issues = self.run(article)
        if issues:
            details = "; ".join(f"{i.path}: {i.message}" for i in issues[:8])
            raise ValidationError(f"article schema invalid: {details}")
