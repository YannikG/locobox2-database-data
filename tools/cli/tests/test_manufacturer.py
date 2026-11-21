from __future__ import annotations

import pytest

from locobox_cli.domain.manufacturer import Manufacturer


def test_parse_bemo() -> None:
    mfr = Manufacturer.parse("bemo")
    assert mfr is Manufacturer.BEMO
    assert mfr.slug == "bemo"
    assert mfr.display_name == "BEMO"


def test_parse_amintiri_aliases() -> None:
    mfr = Manufacturer.parse("af")
    assert mfr is Manufacturer.AMINTIRI_FEROVIARE
    assert mfr.slug == "amintiri-feroviare"
    assert mfr.display_name == "Amintiri Feroviare"
    assert Manufacturer.parse("amintiri-feroviare") is mfr


def test_parse_unknown_lists_bemo() -> None:
    with pytest.raises(ValueError, match="bemo"):
        Manufacturer.parse("unknown-mfr")
