from locobox_cli.adapters.sources.maerklin.parse_pdp import _categories


def test_lok_stays_lokomotive() -> None:
    assert _categories("Elektrolokomotive Baureihe 101", "") == ["lokomotive", "elektrolokomotive"]


def test_generic_class_title_has_no_type() -> None:
    from locobox_cli.adapters.sources.maerklin.parse_pdp import _is_generic_class_title

    assert _is_generic_class_title("Schnellzug-Dampflokomotive mit Schlepptender")
    assert not _is_generic_class_title("BR 185.2")


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
