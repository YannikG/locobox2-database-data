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

    def test_ctlr_already_split(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {
                "type": "CTLR4C-001",
                "number": None,
                "livery": "CTL Rail 4 Chem",
                "country": "PL",
            },
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertIsNone(m.propose_fix(art))

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

    def test_fs_d141_split(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "D.141 1019", "number": None, "country": "IT", "operator": "FS"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_fs_d_num", "D.141", "1019", None, None))

    def test_vectron_e191_evm(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "Vectron E.191 EVM Rail", "number": None, "livery": None, "operator": "Privatbahn"},
            "description": "BR E.191 der EVM Rail",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_vectron_e", "E.191", None, "EVM Rail", None))

    def test_en57_operator_era(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "EN 57 PKP IV", "number": None, "era": "IV", "operator": "PKP"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        fix = m.propose_fix(art)
        self.assertIsNotNone(fix)
        self.assertEqual(fix[1], "EN 57")

    def test_livery_klimaschuetzer(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {
                "type": "BR 412",
                "number": None,
                "livery": "ICE 4 DB AG VI, 4tlg., Klimaschützer",
            },
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_livery", "BR 412", None, "Klimaschützer", None))

    def test_livery_set_junk_clear(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "BR 130", "number": None, "livery": "CSD + 3 Güterwagen"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_livery", "BR 130", None, "", None))

    def test_start_set_taurus(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {"type": "Start-Set mit Bettung Taurus", "number": None, "operator": "ÖBB"},
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_start_taurus", "1216", None, None, None))

    def test_rbe_npz_set(self) -> None:
        art = {
            "manufacturer": "PIKO",
            "model": {
                "type": "2er Set Rbe 4/4 NPZ SBB IV Triebwagen + Steuerwagen",
                "number": None,
                "era": "IV",
                "livery": None,
            },
            "description": "",
            "source": {"url": "https://www.piko-shop.de/"},
        }
        self.assertEqual(m.propose_fix(art), ("piko_rbe_npz", "Rbe 4/4", None, "NPZ", None))


if __name__ == "__main__":
    unittest.main()
