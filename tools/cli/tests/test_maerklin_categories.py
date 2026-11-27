from locobox_cli.adapters.sources.maerklin.parse_pdp import _categories


def test_lok_stays_lokomotive() -> None:
    assert _categories("Elektrolokomotive Baureihe 101", "") == ["lokomotive"]


def test_railcar_diesel() -> None:
    assert _categories("Nahverkehrs-Dieseltriebwagen Baureihe 648.2", "") == [
        "triebwagen",
        "dieseltriebwagen",
    ]


def test_multi_unit_electric() -> None:
    assert _categories("Hochgeschwindigkeitszug TGV INOUI", "") == [
        "triebzug",
        "elektrotriebwagen",
    ]
