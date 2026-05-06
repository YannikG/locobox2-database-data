"""Tests for ``autofix_model_type_number_split``."""

from __future__ import annotations

import unittest

import autofix_model_type_number_split as m


class TestProposeSplit(unittest.TestCase):
    def test_t_478(self) -> None:
        art = {
            "categories": ["lokomotive", "diesellokomotive"],
            "model": {"type": "T 478 2079", "number": None},
        }
        self.assertEqual(m.propose_split(art), ("t_3_4", "T 478", "2079"))

    def test_skips_when_number_set(self) -> None:
        art = {
            "model": {"type": "T 478 2079", "number": "2079"},
        }
        self.assertIsNone(m.propose_split(art))

    def test_skips_marketing_quotes(self) -> None:
        art = {"model": {"type": "22 „Warsteiner“", "number": None}}
        self.assertIsNone(m.propose_split(art))

    def test_steam_slug(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "38 3713", "number": None},
            "source": {
                "url": "https://www.roco.cc/.../7100043-dampflokomotive-38-3713-drg.html",
            },
        }
        self.assertEqual(m.propose_split(art), ("steam_2_4_slug", "38", "3713"))

    def test_steam_no_slug(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "38 3713", "number": None},
            "source": {"url": "https://example.com/no-numbers-here.html"},
        }
        self.assertIsNone(m.propose_split(art))

    def test_cc(self) -> None:
        art = {"model": {"type": "CC 72052", "number": None}}
        self.assertEqual(m.propose_split(art), ("sncf_bb_cc_5", "CC", "72052"))

    def test_rh_109(self) -> None:
        art = {"model": {"type": "Rh 109", "number": None}}
        self.assertEqual(m.propose_split(art), ("rh_n", "Rh", "109"))

    def test_rh_valousek_skipped(self) -> None:
        art = {"model": {"type": "Rh 1144 „Valousek-Edition“", "number": None}}
        self.assertIsNone(m.propose_split(art))

    def test_br_optional(self) -> None:
        art = {"model": {"type": "BR 110", "number": None}}
        self.assertIsNone(m.propose_split(art))
        self.assertEqual(
            m.propose_split(art, include_br=True), ("br_class", "BR", "110")
        )

    def test_br_hyphen_232(self) -> None:
        art = {"model": {"type": "BR-232 049", "number": None}}
        self.assertEqual(m.propose_split(art), ("br_hyphen_nn", "232", "049"))

    def test_1116_railjet_typographic_quotes(self) -> None:
        art = {"model": {"type": "1116 238-7 \u201eRailjet\u201c", "number": None}}
        self.assertEqual(m.propose_split(art), ("series_4_3dash_tail", "1116", "238-7"))

    def test_193_deutschlandpiercer_typographic_quotes(self) -> None:
        art = {
            "model": {
                "type": "193 459-5 \u201eDeutschlandpiercer\u201c",
                "number": None,
            }
        }
        self.assertEqual(m.propose_split(art), ("series_3_3dash_tail", "193", "459-5"))


if __name__ == "__main__":
    unittest.main()
