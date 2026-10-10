from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Optional

from locobox_cli.domain.json_path import get_path, set_path
from locobox_cli.domain.rules import FixRule, RuleHit


def _manufacturer_matches(article: dict[str, Any], expected: str) -> bool:
    want = expected.strip().lower()
    got = str(article.get("manufacturer") or "").strip().lower()
    if got == want:
        return True
    return got.replace(" ", "-") == want


def _when_matches(article: dict[str, Any], rule: FixRule) -> bool:
    when = rule.when
    if when.manufacturer and not _manufacturer_matches(article, when.manufacturer):
        return False
    value = get_path(article, when.field)
    if when.field_is_null:
        return value is None
    if when.field_is_empty_list:
        return isinstance(value, list) and len(value) == 0
    if when.equals is not None:
        return value == when.equals
    if when.match is not None:
        if not isinstance(value, str):
            return False
        return re.search(when.match, value) is not None
    return True


@dataclass
class ApplyRulesResult:
    article: dict[str, Any]
    hits: list[RuleHit] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.hits)


@dataclass(frozen=True, slots=True)
class ApplyRules:
    rules: tuple[FixRule, ...]

    def run(self, article: dict[str, Any]) -> ApplyRulesResult:
        data = deepcopy(article)
        hits: list[RuleHit] = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if not _when_matches(data, rule):
                continue
            hit = self._apply_one(data, rule)
            if hit is not None:
                hits.append(hit)
        return ApplyRulesResult(article=data, hits=hits)

    def _apply_one(self, data: dict[str, Any], rule: FixRule) -> Optional[RuleHit]:
        when = rule.when
        then = rule.then

        if then.clear:
            target = then.set_field or when.field
            old = get_path(data, target)
            if old is None:
                return None
            set_path(data, target, None)
            return RuleHit(rule.id, target, old, None)

        if then.add_to_list is not None:
            list_field = then.set_field or when.field
            cur = get_path(data, list_field)
            if cur is None:
                cur = []
            if not isinstance(cur, list):
                raise ValueError(f"rule {rule.id}: {list_field} is not a list")
            if then.add_to_list in cur:
                return None
            new_list = [*cur, then.add_to_list]
            set_path(data, list_field, new_list)
            return RuleHit(rule.id, list_field, cur, new_list)

        if then.replace is not None:
            if when.match is None:
                raise ValueError(f"rule {rule.id}: then.replace requires when.match")
            cur = get_path(data, when.field)
            if not isinstance(cur, str):
                return None
            new = re.sub(when.match, then.replace, cur)
            if new == cur:
                return None
            set_path(data, when.field, new)
            return RuleHit(rule.id, when.field, cur, new)

        if then.has_set:
            target = then.set_field or when.field
            old = get_path(data, target)
            if old == then.set_value:
                return None
            set_path(data, target, then.set_value)
            return RuleHit(rule.id, target, old, then.set_value)

        return None
