from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from locobox_cli.domain.rules import FixRule, RuleThen, RuleWhen


def _parse_rule(raw: dict[str, Any], *, source: Path) -> FixRule:
    if "id" not in raw:
        raise ValueError(f"rule missing id in {source}")
    when_raw = raw.get("when") or {}
    then_raw = raw.get("then") or {}
    if "field" not in when_raw:
        raise ValueError(f"rule {raw['id']!r} missing when.field in {source}")
    when = RuleWhen(
        field=str(when_raw["field"]),
        manufacturer=(str(when_raw["manufacturer"]).strip() if when_raw.get("manufacturer") else None),
        match=when_raw.get("match"),
        equals=when_raw.get("equals"),
        field_is_null=bool(when_raw.get("field_is_null", False)),
        field_is_empty_list=bool(when_raw.get("field_is_empty_list", False)),
    )
    has_set = "set" in then_raw
    then = RuleThen(
        replace=then_raw["replace"] if "replace" in then_raw else None,
        set_value=then_raw.get("set") if has_set else None,
        has_set=has_set,
        set_field=then_raw.get("set_field"),
        clear=bool(then_raw.get("clear", False)),
        add_to_list=then_raw.get("add_to_list"),
    )
    return FixRule(
        id=str(raw["id"]),
        when=when,
        then=then,
        enabled=bool(raw.get("enabled", True)),
    )


def load_rules_from_file(path: Path) -> list[FixRule]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return []
    if isinstance(data, dict) and "rules" in data:
        items = data["rules"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"unsupported rules format in {path}")
    if not isinstance(items, list):
        raise ValueError(f"rules must be a list in {path}")
    return [_parse_rule(item, source=path) for item in items if isinstance(item, dict)]


def load_rules_tree(root: Path) -> list[FixRule]:
    if not root.exists():
        raise FileNotFoundError(f"rules path missing: {root}")
    if root.is_file():
        files = [root]
    else:
        files = sorted({*root.rglob("*.yaml"), *root.rglob("*.yml")})
    rules: list[FixRule] = []
    seen: set[str] = set()
    for path in files:
        for rule in load_rules_from_file(path):
            if rule.id in seen:
                raise ValueError(f"duplicate rule id {rule.id!r} (also in {path})")
            seen.add(rule.id)
            rules.append(rule)
    return rules
