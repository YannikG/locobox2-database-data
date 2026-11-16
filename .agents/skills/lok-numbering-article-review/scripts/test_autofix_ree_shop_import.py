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

    def test_es_from_sku_suffix(self) -> None:
        base = {
            "manufacturer": "REE",
            "description": "x",
            "categories": ["lokomotive"],
            "model": {"type": "CC 7100", "number": "7136", "electricSystem": "Unbekannt"},
        }
        for art, want in (("JM-005", "DC-Analog"), ("JM-005S", "DC-Digital"), ("JM-005SAC", "AC-Digital")):
            a = {**base, "articleNumber": art, "model": dict(base["model"])}
            fields = {f: v for _r, f, v in m.propose(a)}
            self.assertEqual(fields.get("model.electricSystem"), want, art)

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

    def test_livery_from_livree(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {"type": "BB 67000", "number": "67012", "livery": None},
            "description": "[HO] : Locomotive diesel BB 67012 Livrée bleue, Nevers, Ep. IV, Analogique - MB245",
            "categories": ["lokomotive", "diesellokomotive"],
        }
        fields = {f: v for _r, f, v in m.propose(art)}
        self.assertEqual(fields.get("model.livery"), "bleue")

    def test_livery_from_quoted(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {"type": "BB 9200", "number": "9288", "livery": None},
            "description": '[HO] Locomotive électrique BB 9288 "Arzens", DCCS - MB197S',
            "categories": ["lokomotive", "elektrolokomotive"],
        }
        fields = {f: v for _r, f, v in m.propose(art)}
        self.assertEqual(fields.get("model.livery"), "Arzens")

    def test_livery_vert_301(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {"type": "Moyse 32 TDE", "number": None, "livery": None},
            "description": "[HO] : Locotracteur MOYSE Indutriel vert 301, DCCS - MB091S",
            "categories": ["lokomotive", "diesellokomotive"],
        }
        fields = {f: v for _r, f, v in m.propose(art)}
        self.assertEqual(fields.get("model.livery"), "vert 301")

    def test_livery_rouge_creme(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {"type": "Billard A80 D1", "number": "248", "livery": None},
            "description": "[HOe/HOm] : Autorail A80 D1, 1 phare, rouge/crème, DCC SOUND, Ep.III - VM062S",
            "categories": ["triebwagen", "dieseltriebwagen"],
        }
        fields = {f: v for _r, f, v in m.propose(art)}
        self.assertEqual(fields.get("model.livery"), "rouge/crème")

    def test_livery_leaves_existing(self) -> None:
        art = {
            "manufacturer": "REE",
            "model": {"type": "BB 9200", "number": "9288", "livery": "Arzens"},
            "description": '[HO] Locomotive électrique BB 9288 "Arzens", DCCS',
            "categories": ["lokomotive"],
        }
        fields = {f: v for _r, f, v in m.propose(art)}
        self.assertNotIn("model.livery", fields)


if __name__ == "__main__":
    unittest.main()
