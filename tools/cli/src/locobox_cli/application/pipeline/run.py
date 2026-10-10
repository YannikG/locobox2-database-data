from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from locobox_cli.application.rules.engine import ApplyRules, ApplyRulesResult
from locobox_cli.domain.rules import FixRule, RuleHit
from locobox_cli.domain.text import normalize_article_strings


@dataclass
class PipelineResult:
    article: dict[str, Any]
    swiss_ss_changes: int = 0
    rule_hits: list[RuleHit] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.swiss_ss_changes > 0 or bool(self.rule_hits)


@dataclass(frozen=True, slots=True)
class RunArticlePipeline:
    """Shared post-load pipeline: text normalize + YAML fix rules."""

    rules: tuple[FixRule, ...]
    apply_swiss_ss: bool = True

    def run(self, article: dict[str, Any]) -> PipelineResult:
        data = deepcopy(article)
        swiss = 0
        if self.apply_swiss_ss:
            swiss = normalize_article_strings(data)
        rules_result: ApplyRulesResult = ApplyRules(self.rules).run(data)
        return PipelineResult(
            article=rules_result.article,
            swiss_ss_changes=swiss,
            rule_hits=rules_result.hits,
        )
