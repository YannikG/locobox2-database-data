from __future__ import annotations

import json
from pathlib import Path

from locobox_cli.adapters.rules_yaml import load_rules_tree
from locobox_cli.application.pipeline.run import RunArticlePipeline
from locobox_cli.application.rules.engine import ApplyRules
from locobox_cli.domain.rules import FixRule, RuleThen, RuleWhen

FIXTURE = Path(__file__).parent / "fixtures" / "sample_article.json"
REPO_RULES = Path(__file__).resolve().parents[3] / "rules"


def test_replace_rule() -> None:
    rule = FixRule(
        id="strip-x",
        when=RuleWhen(field="model.type", match=r"\s+X$"),
        then=RuleThen(replace=""),
    )
    article = {"manufacturer": "PIKO", "model": {"type": "BR 1 X"}}
    result = ApplyRules((rule,)).run(article)
    assert result.changed
    assert result.article["model"]["type"] == "BR 1"


def test_pipeline_swiss_and_repo_rules() -> None:
    article = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rules = load_rules_tree(REPO_RULES)
    result = RunArticlePipeline(rules=tuple(rules)).run(article)
    assert "ß" not in result.article["description"]
    assert "ss" in result.article["description"]
    assert "ü" in result.article["description"] or "Ã¼" not in result.article["description"]
    assert "inkl. PIKO Sound-Decoder" not in result.article["model"]["type"]
    assert any(h.rule_id == "piko-strip-inkl-sound-decoder" for h in result.rule_hits)
