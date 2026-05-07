"""Tests for ``autofix_model_country``."""

from __future__ import annotations

import unittest

import autofix_model_country as c


class TestProposeCountry(unittest.TestCase):
    def test_db(self) -> None:
        art = {"model": {"country": None, "operator": "DB"}}
        self.assertEqual(c.propose_country(art), ("operator_map:DB", "DE"))

    def test_dr_iv(self) -> None:
        art = {"model": {"country": None, "operator": "DR", "era": "IV"}}
        self.assertEqual(c.propose_country(art), ("dr_era_contains_iv", "DD"))

    def test_dr_iii(self) -> None:
        art = {"model": {"country": None, "operator": "DR", "era": "III"}}
        self.assertEqual(c.propose_country(art), ("dr_era_reichsbahn_i_iii", "DE"))

    def test_dr_vi_only(self) -> None:
        art = {"model": {"country": None, "operator": "DR", "era": "VI"}}
        self.assertEqual(c.propose_country(art), ("dr_era_default", "DD"))

    def test_dr_missing_era(self) -> None:
        art = {"model": {"country": None, "operator": "DR"}}
        self.assertEqual(c.propose_country(art), ("dr_era_default", "DD"))

    def test_csd_cs(self) -> None:
        art = {"model": {"country": None, "operator": "CSD"}}
        self.assertEqual(c.propose_country(art), ("operator_map:CSD", "CS"))

    def test_gts_rail_it(self) -> None:
        art = {"model": {"country": None, "operator": "GTS Rail"}}
        self.assertEqual(c.propose_country(art), ("operator_map:GTS Rail", "IT"))

    def test_skips_when_country_set(self) -> None:
        art = {"model": {"country": "DE", "operator": "DB"}}
        self.assertIsNone(c.propose_country(art))


if __name__ == "__main__":
    unittest.main()
