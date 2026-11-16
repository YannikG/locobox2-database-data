from __future__ import annotations

import pytest

from locobox_cli.domain.manufacturer import Manufacturer


def test_parse_bemo() -> None:
    mfr = Manufacturer.parse("bemo")
    assert mfr is Manufacturer.BEMO
    assert mfr.slug == "bemo"
    assert mfr.display_name == "BEMO"


def test_parse_unknown_lists_bemo() -> None:
    with pytest.raises(ValueError, match="bemo"):
        Manufacturer.parse("unknown-mfr")
