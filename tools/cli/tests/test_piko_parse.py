from __future__ import annotations

from pathlib import Path

from locobox_cli.adapters.sources.piko.parse_pdp import parse_piko_pdp
from locobox_cli.application.articles.validate import ValidateArticle

FIXTURE = Path(__file__).parent / "fixtures" / "piko_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_parse_piko_pdp_fixture_is_schema_valid() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    art = parse_piko_pdp(
        html,
        canonical_url="https://www.piko-shop.de/de/artikel/21002.html",
        article="21002",
        campaign_tag="piko-neuheiten-2024",
    )
    assert art["articleNumber"] == "21002"
    assert art["model"]["type"].startswith("E-Lok")
    assert art["uvp"]["amount"] == 325.0
    assert "piko-neuheiten-2024" in art["tags"]
    issues = ValidateArticle.from_contracts(REPO).run(art)
    assert issues == [], issues
