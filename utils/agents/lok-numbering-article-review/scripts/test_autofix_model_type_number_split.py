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

    def test_dotted_steam_slug_50(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "50.685", "number": None},
            "source": {
                "url": "https://www.roco.cc/.../7100016-dampflokomotive-50685-obb.html",
            },
        }
        self.assertEqual(m.propose_split(art), ("dotted_steam_slug", "50", "685"))

    def test_dotted_steam_slug_302(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "302.608", "number": None},
            "source": {
                "url": "https://www.roco.cc/.../7110025-dampflokomotive-302608-mav.html",
            },
        }
        self.assertEqual(m.propose_split(art), ("dotted_steam_slug", "302", "608"))

    def test_br2_uic_4dash(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "01 0529-6", "number": None},
        }
        self.assertEqual(m.propose_split(art), ("br2_uic_4dash", "01", "0529-6"))

    def test_br2_uic_4dash_requires_dampf(self) -> None:
        art = {
            "categories": ["lokomotive", "diesellokomotive"],
            "model": {"type": "01 0529-6", "number": None},
        }
        self.assertIsNone(m.propose_split(art))

    def test_br2_space_3digit(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "10 001", "number": None},
        }
        self.assertEqual(m.propose_split(art), ("br2_space_3digit", "10", "001"))

    def test_br2_space_3digit_requires_dampf(self) -> None:
        art = {
            "categories": ["lokomotive", "diesellokomotive"],
            "model": {"type": "10 001", "number": None},
        }
        self.assertIsNone(m.propose_split(art))

    def test_t_669_dot(self) -> None:
        art = {"model": {"type": "T 669.0107", "number": None}}
        self.assertEqual(m.propose_split(art), ("t_669_dot", "T 669", "0107"))

    def test_br_35_dot_sub(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "BR 35.10", "number": None},
        }
        self.assertEqual(m.propose_split(art), ("br_35_dot_sub", "BR 35", "10"))

    def test_rh_354_dot_sub(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "Rh 354.1", "number": None},
        }
        self.assertEqual(m.propose_split(art), ("rh_354_dot_sub", "Rh 354", "1"))

    def test_v_300_trailing(self) -> None:
        art = {
            "categories": ["lokomotive", "diesellokomotive"],
            "model": {"type": "V 300 005", "number": None},
        }
        self.assertEqual(m.propose_split(art), ("v_3_trailing", "V 300", "005"))

    def test_br_89_dot_subrange(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "BR 89.70–75", "number": None},
        }
        self.assertEqual(
            m.propose_split(art),
            ("br_89_dot_subrange", "BR 89", "70–75"),
        )

    def test_br_89_dot_subrange_ascii_hyphen(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "BR 89.70-75", "number": None},
        }
        self.assertEqual(
            m.propose_split(art),
            ("br_89_dot_subrange", "BR 89", "70–75"),
        )

    def test_br_89_dot_subrange_nobr(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "89.70–75", "number": None},
        }
        self.assertEqual(
            m.propose_split(art),
            ("br_89_dot_subrange_nobr", "BR 89", "70–75"),
        )

    def test_m62_space(self) -> None:
        art = {"model": {"type": "M62 221", "number": None}}
        self.assertEqual(m.propose_split(art), ("m62_space", "M62", "221"))

    def test_m62_dash(self) -> None:
        art = {"model": {"type": "M62-221", "number": None}}
        self.assertEqual(m.propose_split(art), ("m62_dash", "M62", "221"))

    def test_dotted_steam_no_slug(self) -> None:
        art = {
            "categories": ["lokomotive", "dampflokomotive"],
            "model": {"type": "50.685", "number": None},
            "source": {"url": "https://example.com/dampflokomotive-99999-x.html"},
        }
        self.assertIsNone(m.propose_split(art))

    def test_dotted_not_dampf_category(self) -> None:
        art = {
            "categories": ["lokomotive", "diesellokomotive"],
            "model": {"type": "50.685", "number": None},
            "source": {
                "url": "https://www.roco.cc/.../7100016-dampflokomotive-50685-obb.html",
            },
        }
        self.assertIsNone(m.propose_split(art))

    def test_piko_br_baureihe_ohne_nummer(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "E-Lok BR 184.1 DB IV", "number": None},
            "source": {"url": "https://www.piko-shop.de/de/artikel/x.html"},
        }
        self.assertEqual(
            m.propose_split(art),
            ("piko_br_rh_series", "BR 184.1", None),
        )

    def test_piko_br_mit_betriebsnummer(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "E-Lok BR 111 122 DB IV", "number": None},
            "source": {"url": "https://www.piko-shop.de/de/artikel/y.html"},
        }
        self.assertEqual(
            m.propose_split(art),
            ("piko_br_rh_series", "BR 111", "122"),
        )


if __name__ == "__main__":
    unittest.main()
