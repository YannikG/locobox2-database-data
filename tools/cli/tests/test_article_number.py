from __future__ import annotations

import pytest

from locobox_cli.domain.article import ArticleNumber


def test_numeric_still_works() -> None:
    assert ArticleNumber.parse("21002").value == "21002"
    assert ArticleNumber.parse("71005").value == "71005"
    with pytest.raises(ValueError):
        ArticleNumber.parse("123")  # too short
    with pytest.raises(ValueError):
        ArticleNumber.parse("abc")


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("MB-263", "MB-263"),
        ("MB-263S", "MB-263S"),
        ("MB-263SAC", "MB-263SAC"),
        ("MB 176S", "MB-176S"),
        ("mb263s", "MB-263S"),
        ("TGV005S", "TGV-005S"),
        ("TGV-004 S", "TGV-004S"),
        ("JM-001", "JM-001"),
        ("VM-010", "VM-010"),
    ],
)
def test_ree_normalize_spaces_and_case(raw: str, canonical: str) -> None:
    art = ArticleNumber.parse(raw)
    assert art.value == canonical
    assert art.compact() == canonical.replace("-", "")


def test_constructor_rejects_non_canonical_alphanum() -> None:
    with pytest.raises(ValueError):
        ArticleNumber("MB 176S")
    assert ArticleNumber("MB-176S").value == "MB-176S"
