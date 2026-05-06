"""Tests für Katalog-Stubs (nur fehlende JSON)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import roco_shop_parse_pdp as pdp

_SCRIPT = Path(__file__).resolve().parent / "roco_catalogue_stub.py"


class TestArticleRecordStub(unittest.TestCase):
    def test_article_record_stub_matches_skeleton(self) -> None:
        a = pdp.article_record_stub("7500178")
        self.assertEqual(a["articleNumber"], "7500178")
        self.assertEqual(a["id"], "roco-7500178")
        self.assertEqual(a["manufacturer"], "Roco")
        self.assertTrue(
            str(a["source"]["url"]).startswith("https://www.roco.cc/"),
            msg="Stub-URL muss gültige Basis-URI für Schema sein",
        )

    def test_article_record_stub_rejects_invalid_number(self) -> None:
        with self.assertRaises(ValueError):
            pdp.article_record_stub("12")
        with self.assertRaises(ValueError):
            pdp.article_record_stub("abc")


class TestCatalogueStubCli(unittest.TestCase):
    def test_skips_existing_only_creates_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            existing = root / "70000.json"
            existing.write_text(
                json.dumps({"articleNumber": "70000", "keep": True}, ensure_ascii=False),
                encoding="utf-8",
            )
            lst = root / "list.txt"
            lst.write_text("70000\n70001\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT),
                    "--articles",
                    str(lst),
                    "--articles-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            summary = json.loads(proc.stdout.strip())
            self.assertEqual(summary["skipped_existing"], 1)
            self.assertEqual(summary["created"], 1)
            self.assertTrue((root / "70001.json").is_file())
            self.assertIn("keep", json.loads(existing.read_text(encoding="utf-8")))

    def test_deduplicates_article_numbers_in_list(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lst = root / "list.txt"
            lst.write_text("70002\n70002\n70003\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT),
                    "--articles",
                    str(lst),
                    "--articles-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            summary = json.loads(proc.stdout.strip())
            self.assertEqual(summary["created"], 2)

    def test_fail_if_nothing_created_when_all_exist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "70004.json").write_text("{}", encoding="utf-8")
            lst = root / "list.txt"
            lst.write_text("70004\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT),
                    "--articles",
                    str(lst),
                    "--articles-root",
                    str(root),
                    "--fail-if-nothing-created",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
