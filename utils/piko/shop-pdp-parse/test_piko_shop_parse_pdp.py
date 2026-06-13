#!/usr/bin/env python3
"""Tests für PIKO Shop-Parser (Stromsystem aus Beschreibung)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "shop-pdp-parse" / "piko_shop_parse_pdp.py"
_spec = importlib.util.spec_from_file_location("piko_shop_parse_pdp", _SCRIPT)
assert _spec and _spec.loader
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


class TestPikoElectricSystem(unittest.TestCase):
    def test_dc_analog_expert_plux_without_builtin_decoder(self) -> None:
        desc = (
            "E-Lok BR 184.1 DB IV Modelleisenbahn kaufen | PIKO Webshop\n\n"
            "Stromsystem: Gleichstrom\n"
            "Digitale Schnittstelle: NEM 658 PluX22\n"
            "(Innen-)Beleuchtung: Digital schaltbare Führerstandsbeleuchtung (mit PluX22 Decoder)\n"
            "Sound: PIKO Sound-Decoder nachrüstbar #56644"
        )
        self.assertEqual(m._canonical_electric_system_from_description(desc), "DC-Analog")

    def test_dc_digital_sound_variant(self) -> None:
        desc = (
            "Sound-E-Lok BR 184.1 DB IV, inkl. PIKO Sound-Decoder Modelleisenbahn kaufen | PIKO Webshop\n\n"
            "Sound ja/nein: ja\n"
            "Stromsystem: Gleichstrom\n"
            "Verbauter Decoder: PluX22 Sounddecoder\n"
            "Sound: PIKO Sound-Decoder werkseitig ausgerüstet"
        )
        self.assertEqual(m._canonical_electric_system_from_description(desc), "DC-Digital")

    def test_dc_analog_smartline_nem652(self) -> None:
        desc = (
            "E-Lok BR 185 Beacon VI Modelleisenbahn kaufen | PIKO Webshop\n\n"
            "Stromsystem: Gleichstrom\n"
            "Digitale Schnittstelle: NEM 652"
        )
        self.assertEqual(m._canonical_electric_system_from_description(desc), "DC-Analog")

    def test_ac_digital_with_builtin_decoder(self) -> None:
        desc = (
            "E-Lok BR 185 Beacon VI Wechselstromversion Modelleisenbahn kaufen | PIKO Webshop\n\n"
            "Stromsystem: Wechselstrom\n"
            "Digitale Schnittstelle: NEM 652\n"
            "Verbauter Decoder: 8-polig"
        )
        self.assertEqual(m._canonical_electric_system_from_description(desc), "AC-Digital")

    def test_n_shop_without_stromsystem_dc_analog(self) -> None:
        desc = (
            "N E-Lok BR 101 DB AG V Modelleisenbahn kaufen | PIKO Webshop\n\n"
            "Artikelnummer: 40562\n"
            "Hersteller: PIKO\n"
            "Digitale Schnittstelle: NEM 662 Next18"
        )
        self.assertEqual(m._infer_electric_system_from_description(desc), "DC-Analog")

    def test_n_sound_without_stromsystem_dc_digital(self) -> None:
        desc = (
            "N Sound-E-Lok BR 101 DB AG V, inkl. PIKO Sound-Decoder Modelleisenbahn kaufen | PIKO Webshop\n\n"
            "Artikelnummer: 40563\n"
            "Hersteller: PIKO\n"
            "Sound ja/nein: ja\n"
            "Verbauter Decoder: Next18 Sounddecoder\n"
            "Sound: PIKO Sound-Decoder werkseitig ausgerüstet"
        )
        self.assertEqual(m._infer_electric_system_from_description(desc), "DC-Digital")


class TestPikoCampaignTags(unittest.TestCase):
    def test_replace_2026_with_2025(self) -> None:
        out = m._finalize_tags(
            ["piko-neuheiten-2026", "other"],
            campaign_tag="piko-neuheiten-2025",
            replace_tags=["piko-neuheiten-2026"],
        )
        self.assertEqual(out, ["piko-neuheiten-2025", "other"])

    def test_add_campaign_on_empty(self) -> None:
        out = m._finalize_tags(
            [],
            campaign_tag="piko-neuheiten-2025",
            replace_tags=["piko-neuheiten-2026"],
        )
        self.assertEqual(out, ["piko-neuheiten-2025"])


if __name__ == "__main__":
    unittest.main()
