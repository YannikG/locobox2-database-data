from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from locobox_cli.application.articles.patch import SetField, parse_value_arg
from locobox_cli.application.articles.validate import ValidateArticle

FIXTURE = Path(__file__).parent / "fixtures" / "sample_article.json"
REPO = Path(__file__).resolve().parents[3]


def test_set_field_validates_and_updates() -> None:
    article = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # clean type so schema stays happy after strip leftover
    article["model"]["type"] = "BR E410"
    article["description"] = "ok"
    result = SetField(ValidateArticle.from_contracts(REPO)).run(
        article, "model.type", "BR E410.1"
    )
    assert result.before == "BR E410"
    assert result.after == "BR E410.1"
    assert result.article["model"]["type"] == "BR E410.1"
    assert "updatedAt" in result.article


def test_set_field_rejects_disallowed_path() -> None:
    article = json.loads(FIXTURE.read_text(encoding="utf-8"))
    article["model"]["type"] = "BR E410"
    article["description"] = "ok"
    with pytest.raises(ValueError, match="not allowed"):
        SetField(ValidateArticle.from_contracts(REPO)).run(article, "id", "evil")


def test_set_field_rolls_back_on_schema_fail() -> None:
    article = json.loads(FIXTURE.read_text(encoding="utf-8"))
    article["model"]["type"] = "BR E410"
    article["description"] = "ok"
    with pytest.raises(ValidationError):
        SetField(ValidateArticle.from_contracts(REPO)).run(
            article, "model.country", "Deutschland"
        )


def test_parse_value_arg() -> None:
    assert parse_value_arg("null", as_json=False) is None
    assert parse_value_arg("12.5", as_json=True) == 12.5
    assert parse_value_arg('"x"', as_json=True) == "x"
