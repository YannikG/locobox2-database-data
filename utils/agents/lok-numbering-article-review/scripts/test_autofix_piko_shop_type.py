"""Tests for ``autofix_piko_shop_type``."""

from __future__ import annotations

import unittest

import autofix_piko_shop_type as m


class TestPikoShopType(unittest.TestCase):
    def test_strip_sound_elok_br(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "Sound-E-Lok BR 184.1 DB IV, inkl. PIKO Sound-Decoder", "number": None, "era": "IV", "country": "DE"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_br_rh", "BR 184.1", None, None, None))

    def test_uic_185_329(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "E-Lok 185 329 Black Dragons VI", "number": None, "era": "VI", "country": "DE", "livery": None},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_uic_br", "BR 185", "329", "Black Dragons", None))

    def test_vectron_7193(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "BR 7193", "number": None, "livery": None},
            "description": "Sound-Elektrolok Vectron BR 7193 Medway VI",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_vectron", "BR 193", "7193", "Medway", None))

    def test_d445_variant(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "D.445 1. Serie mit Logo", "number": None, "livery": None, "country": "IT"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(
            m.propose_fix(art),
            ("piko_d445", "D.445", None, "1. Serie mit Logo", None),
        )

    def test_desiro(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": '"Desiro" Saarlandbahn', "number": None, "livery": None, "country": "DE"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(
            m.propose_fix(art),
            ("piko_desiro", "Desiro", None, "Saarlandbahn", None),
        )

    def test_v200_messe(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "Diesellok V200 1001 DR III, Messe Leipzig", "number": None, "era": "III", "livery": None, "country": "DD"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_v200", "V 200", "1001", "Messe Leipzig", None))


if __name__ == "__main__":
    unittest.main()
