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

    def test_pkp_cargo_pl(self) -> None:
        art = {"model": {"country": None, "operator": "PKP Cargo"}}
        self.assertEqual(c.propose_country(art), ("operator_map:PKP Cargo", "PL"))

    def test_bls_cargo_ch(self) -> None:
        art = {"model": {"country": None, "operator": "BLS Cargo"}}
        self.assertEqual(c.propose_country(art), ("operator_map:BLS Cargo", "CH"))

    def test_mercitalia_rail_it(self) -> None:
        art = {"model": {"country": None, "operator": "Mercitalia Rail"}}
        self.assertEqual(c.propose_country(art), ("operator_map:Mercitalia Rail", "IT"))

    def test_drg_de(self) -> None:
        art = {"model": {"country": None, "operator": "DRG"}}
        self.assertEqual(c.propose_country(art), ("operator_map:DRG", "DE"))

    def test_sncb_be(self) -> None:
        art = {"model": {"country": None, "operator": "SNCB"}}
        self.assertEqual(c.propose_country(art), ("operator_map:SNCB", "BE"))

    def test_ns_nl(self) -> None:
        art = {"model": {"country": None, "operator": "NS"}}
        self.assertEqual(c.propose_country(art), ("operator_map:NS", "NL"))

    def test_railpool_not_autofixed(self) -> None:
        art = {"model": {"country": None, "operator": "Railpool"}}
        self.assertIsNone(c.propose_country(art))

    def test_lte_not_autofixed(self) -> None:
        art = {"model": {"country": None, "operator": "LTE"}}
        self.assertIsNone(c.propose_country(art))

    def test_tx_logistik_not_autofixed(self) -> None:
        art = {"model": {"country": None, "operator": "TX Logistik"}}
        self.assertIsNone(c.propose_country(art))

    def test_skips_when_country_set(self) -> None:
        art = {"model": {"country": "DE", "operator": "DB"}}
        self.assertIsNone(c.propose_country(art))

    def test_d_rgw_us(self) -> None:
        art = {"model": {"country": None, "operator": "D&RGW"}}
        self.assertEqual(c.propose_country(art), ("operator_map:D&RGW", "US"))

    def test_sp_southern_pacific_us(self) -> None:
        art = {"model": {"country": None, "operator": "SP (Southern Pacific)"}}
        self.assertEqual(c.propose_country(art), ("operator_map:SP (Southern Pacific)", "US"))

    def test_privatbahn_captrain_de(self) -> None:
        art = {
            "model": {"country": None, "operator": "Privatbahn", "type": "E-Lok BR 152 Captrain VI"},
            "description": "x",
        }
        self.assertEqual(c.propose_country(art)[1], "DE")

    def test_privatbahn_railion_nl(self) -> None:
        art = {
            "model": {
                "country": None,
                "operator": "Privatbahn",
                "type": "Diesellok 6400 Railion Logistics NL VI",
            },
            "description": "x",
        }
        self.assertEqual(c.propose_country(art)[1], "NL")


if __name__ == "__main__":
    unittest.main()
