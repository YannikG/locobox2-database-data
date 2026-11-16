"""Tests for ``autofix_ree_shop_import``."""

from __future__ import annotations

import unittest

import autofix_ree_shop_import as m


class SncfSeriesTests(unittest.TestCase):
    def test_bb_9200_running(self) -> None:
        self.assertEqual(m.sncf_series_and_running("BB", "9282"), ("BB 9200", "9282"))

    def test_bb_16000(self) -> None:
        self.assertEqual(m.sncf_series_and_running("BB", "16001"), ("BB 16000", "16001"))

    def test_bb_25100(self) -> None:
        self.assertEqual(m.sncf_series_and_running("BB", "25188"), ("BB 25100", "25188"))

    def test_cc_7100(self) -> None:
        self.assertEqual(m.sncf_series_and_running("CC", "7136"), ("CC 7100", "7136"))

    def test_bb_63000(self) -> None:
        self.assertEqual(m.sncf_series_and_running("BB", "63792"), ("BB 63000", "63792"))

    def test_pure_series_5(self) -> None:
        self.assertEqual(m.sncf_series_and_running("BB", "26000"), ("BB 26000", None))


class ProposeTests(unittest.TestCase):
    def test_repair_type_eq_number(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {"type": "BB 9282", "number": "BB 9282"},
            "description": "BB 9282",
            "categories": ["lokomotive", "elektrolokomotive"],
        }
        ch = m.propose(art)
        fields = {f: v for _r, f, v in ch}
        self.assertEqual(fields.get("model.type"), "BB 9200")
        self.assertEqual(fields.get("model.number"), "9282")

    def test_bb400_compact_number(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {"type": "BB 400", "number": "BB400", "scale": "H0m"},
            "description": "BB 400",
            "categories": ["lokomotive", "diesellokomotive"],
        }
        ch = m.propose(art)
        fields = {f: v for _r, f, v in ch}
        self.assertNotIn("model.type", fields)  # type already canonical
        self.assertEqual(fields.get("model.number"), "400")

    def test_steam_machine(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {
                "type": "MACHINE 2-231K 8 NORD, CALAIS - Machine préservée",
                "number": None,
                "operator": "SNCF",
                "era": "V",
            },
            "description": "[HO] : MACHINE 2-231K 8 NORD, CALAIS",
            "categories": ["lokomotive"],
        }
        ch = m.propose(art)
        fields = {f: v for _r, f, v in ch}
        self.assertEqual(fields.get("model.type"), "231 K")
        self.assertEqual(fields.get("model.number"), "2-8")
        self.assertIn("dampflokomotive", fields.get("categories") or [])


if __name__ == "__main__":
    unittest.main()
