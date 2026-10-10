from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class RuleWhen:
    field: str
    manufacturer: Optional[str] = None
    match: Optional[str] = None
    equals: Optional[str] = None
    field_is_null: bool = False
    field_is_empty_list: bool = False


@dataclass(frozen=True, slots=True)
class RuleThen:
    replace: Optional[str] = None
    set_value: Any = None
    has_set: bool = False
    set_field: Optional[str] = None
    clear: bool = False
    add_to_list: Optional[str] = None


@dataclass(frozen=True, slots=True)
class FixRule:
    id: str
    when: RuleWhen
    then: RuleThen
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class RuleHit:
    rule_id: str
    field: str
    before: Any
    after: Any
