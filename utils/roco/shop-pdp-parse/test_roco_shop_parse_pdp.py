"""Unittests für PDP-Parser (merge, Galerie-URL)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import roco_shop_parse_pdp as pdp


class TestMergeImageUrl(unittest.TestCase):
    def test_merge_removes_stale_imageurl_when_parse_has_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "70000.json"
            path.write_text(
                json.dumps(
                    {
                        "articleNumber": "70000",
                        "source": {
                            "url": "https://www.roco.cc/old.html",
                            "imageUrl": "https://example.com/stale.jpg",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            parsed = {
                "articleNumber": "70000",
                "canonicalUrl": "https://www.roco.cc/new.html",
            }
            merged, out = pdp.merge_article_record(
                parsed,
                notes="test",
                articles_root=root,
                article_override=None,
                merge_only=None,
            )
            self.assertEqual(out, path)
            self.assertNotIn("imageUrl", merged.get("source", {}))

    def test_merge_sets_imageurl_from_parse(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "70001.json"
            path.write_text(
                json.dumps(
                    {
                        "articleNumber": "70001",
                        "source": {"url": "https://www.roco.cc/a.html"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            parsed = {
                "articleNumber": "70001",
                "canonicalUrl": "https://www.roco.cc/b.html",
                "imageUrl": "https://cdn.example/new.png",
            }
            merged, _ = pdp.merge_article_record(
                parsed,
                notes="test",
                articles_root=root,
                article_override=None,
                merge_only=None,
            )
            self.assertEqual(merged["source"]["imageUrl"], "https://cdn.example/new.png")


class TestMergeOnly(unittest.TestCase):
    def test_validate_rejects_unknown_key(self) -> None:
        with self.assertRaises(SystemExit):
            pdp._validate_merge_only({"model.luepMm", "typo"})

    def test_merge_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "m.json"
            p.write_text(
                '{"mergeOnly": ["model.luepMm", "model.minRadiusMm"]}',
                encoding="utf-8",
            )
            keys = pdp._merge_only_from_config_file(p)
            self.assertEqual(keys, {"model.luepMm", "model.minRadiusMm"})

    def test_merge_only_model_luep_leaves_description(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "7320107.json"
            path.write_text(
                json.dumps(
                    {
                        "articleNumber": "7320107",
                        "description": "Handkuratiert unverändert lassen.",
                        "model": {"luepMm": None, "operator": "ALT"},
                        "source": {"url": "https://www.roco.cc/old.html"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            parsed = {
                "articleNumber": "7320107",
                "canonicalUrl": "https://www.roco.cc/new.html",
                "description": "Aus dem Shop neu geparst.",
                "modelPatch": {"luepMm": 164, "operator": "NEU"},
            }
            merged, _ = pdp.merge_article_record(
                parsed,
                notes="test",
                articles_root=root,
                article_override=None,
                merge_only={"model.luepMm"},
            )
            self.assertEqual(merged["description"], "Handkuratiert unverändert lassen.")
            self.assertEqual(merged["model"]["luepMm"], 164)
            self.assertEqual(merged["model"]["operator"], "ALT")
            self.assertEqual(merged["source"]["url"], "https://www.roco.cc/old.html")

    def test_merge_only_skips_image_delete(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "70002.json"
            path.write_text(
                json.dumps(
                    {
                        "articleNumber": "70002",
                        "source": {
                            "url": "https://www.roco.cc/a.html",
                            "imageUrl": "https://cdn.example/keep.jpg",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            parsed = {
                "articleNumber": "70002",
                "canonicalUrl": "https://www.roco.cc/b.html",
            }
            merged, _ = pdp.merge_article_record(
                parsed,
                notes="test",
                articles_root=root,
                article_override=None,
                merge_only={"source.url"},
            )
            self.assertEqual(merged["source"]["imageUrl"], "https://cdn.example/keep.jpg")


class TestParseRocoOgTitle(unittest.TestCase):
    def test_dampflok_typ_and_operator(self) -> None:
        tm, cats = pdp._parse_roco_og_title("Dampflokomotive 38 2566-8, DR")
        self.assertEqual(tm.get("type"), "38 2566-8")
        self.assertIsNone(tm.get("number"))
        self.assertEqual(tm.get("operator"), "DR")
        self.assertIn("dampflokomotive", cats)

    def test_elektro_with_epoche_operator(self) -> None:
        tm, cats = pdp._parse_roco_og_title("Elektrolokomotive Re 4/4III 43, IV-V")
        self.assertEqual(tm.get("type"), "Re 4/4III 43")
        self.assertEqual(tm.get("operator"), "IV-V")
        self.assertEqual(cats, ["elektrolokomotive"])

    def test_no_comma_returns_empty(self) -> None:
        self.assertEqual(pdp._parse_roco_og_title("Nur ein Titel"), ({}, []))

    def test_whitespace_collapsed_in_title_parts(self) -> None:
        tm, cats = pdp._parse_roco_og_title(
            "  Dampflokomotive   38  2566-8  ,  DR  "
        )
        self.assertEqual(tm.get("type"), "38 2566-8")
        self.assertEqual(tm.get("operator"), "DR")
        self.assertIn("dampflokomotive", cats)

    def test_leading_article_number_skipped_like_roco_og_title(self) -> None:
        tm, cats = pdp._parse_roco_og_title(
            "7500178 Elektrolokomotive 145 070-9, RBH"
        )
        self.assertEqual(tm.get("type"), "145 070-9")
        self.assertIsNone(tm.get("number"))
        self.assertEqual(tm.get("operator"), "RBH")
        self.assertEqual(cats, ["elektrolokomotive"])

    def test_operator_can_include_commas_after_first_split(self) -> None:
        tm, _ = pdp._parse_roco_og_title(
            "7500178 Elektrolokomotive 145 070-9, RBH, Zweigniederlassung Nord"
        )
        self.assertEqual(tm.get("operator"), "RBH, Zweigniederlassung Nord")

    def test_two_leading_skus_stripped(self) -> None:
        tm, _ = pdp._parse_roco_og_title(
            "7500178 7100045 Elektrolokomotive 145 070-9, DR"
        )
        self.assertEqual(tm.get("type"), "145 070-9")
        self.assertEqual(tm.get("operator"), "DR")

    def test_merge_applies_title_patch_when_full_merge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "7100045.json"
            path.write_text(
                json.dumps(
                    {
                        "articleNumber": "7100045",
                        "model": {
                            "type": "Dampflokomotive",
                            "number": "38 2566-8",
                            "operator": "X",
                        },
                        "categories": ["lokomotive"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            parsed = {
                "articleNumber": "7100045",
                "modelPatch": {},
                "titleModelPatch": {
                    "type": "38 2566-8",
                    "number": None,
                    "operator": "DR",
                },
                "titleCategorySlugs": ["dampflokomotive"],
            }
            merged, _ = pdp.merge_article_record(
                parsed,
                notes="t",
                articles_root=root,
                article_override=None,
                merge_only=None,
            )
            self.assertEqual(merged["model"]["type"], "38 2566-8")
            self.assertIsNone(merged["model"]["number"])
            self.assertEqual(merged["model"]["operator"], "DR")
            self.assertIn("dampflokomotive", merged["categories"])

    def test_merge_skips_title_when_merge_only_subset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "7100045.json"
            path.write_text(
                json.dumps(
                    {
                        "articleNumber": "7100045",
                        "model": {
                            "type": "Dampflokomotive",
                            "number": "38 2566-8",
                            "operator": "X",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            parsed = {
                "articleNumber": "7100045",
                "modelPatch": {"luepMm": 214},
                "titleModelPatch": {
                    "type": "38 2566-8",
                    "number": None,
                    "operator": "DR",
                },
                "titleCategorySlugs": ["dampflokomotive"],
            }
            merged, _ = pdp.merge_article_record(
                parsed,
                notes="t",
                articles_root=root,
                article_override=None,
                merge_only={"model.luepMm"},
            )
            self.assertEqual(merged["model"]["luepMm"], 214)
            self.assertEqual(merged["model"]["type"], "Dampflokomotive")
            self.assertEqual(merged["model"]["number"], "38 2566-8")


class TestParsePdpOgTitleInCompactHtml(unittest.TestCase):
    def test_parse_pdp_sets_title_model_patch_like_importer_compact_doc(self) -> None:
        html = (
            '<!DOCTYPE html><html><head>'
            '<meta property="og:url" '
            'content="https://www.roco.cc/rde/produkte/lokomotiven/'
            'elektrolokomotiven/7500178-elektrolokomotive-145-070-9-rbh.html"/>'
            '<meta property="og:title" '
            'content="7500178 Elektrolokomotive 145 070-9, RBH"/>'
            "</head><body></body></html>"
        )
        out = pdp.parse_pdp(html)
        self.assertEqual(out.get("articleNumber"), "7500178")
        tm = out.get("titleModelPatch") or {}
        self.assertEqual(tm.get("type"), "145 070-9")
        self.assertIsNone(tm.get("number"))
        self.assertEqual(tm.get("operator"), "RBH")


class TestExtractSpecsMultiTable(unittest.TestCase):
    """Roco: mehrere ``#product-attribute-specs-table`` (LüP in späterer Sektion)."""

    def test_multiline_table_open_tag_still_finds_lup(self) -> None:
        html = """
        <table
          class="data"
          id="product-attribute-specs-table">
        <tbody><tr>
        <td class="col data" data-th="Spur">H0</td></tr></tbody></table>
        <table id="product-attribute-specs-table"><tbody><tr>
        <td class="data col" data-th="Länge über Puffer">303 mm</td></tr></tbody></table>
        """
        specs = pdp._extract_specs_table(html)
        self.assertEqual(specs.get("Länge über Puffer"), "303 mm")

    def test_fallback_data_th_when_table_regex_misses(self) -> None:
        html = """
        <div id="product-attribute-specs-table">decoy no td</div>
        <p>noise</p>
        <td class="col data" data-th="Länge über Puffer">280 mm</td>
        """
        specs = pdp._extract_specs_table(html)
        self.assertEqual(specs.get("Länge über Puffer"), "280 mm")

    def test_min_radius_alternate_data_th_label(self) -> None:
        html = """
        <table id="product-attribute-specs-table"><tbody><tr>
        <td class="col data" data-th="Mindest-Radius">419 mm</td>
        </tr></tbody></table>
        """
        specs = pdp._extract_specs_table(html)
        self.assertEqual(specs.get("Mindestradius"), "419 mm")
        patch = pdp._specs_to_model_patch(specs)
        self.assertEqual(patch.get("minRadiusMm"), 419)

    def test_merges_rows_from_all_tables_with_same_id(self) -> None:
        html = """
        <table id="product-attribute-specs-table"><tbody>
        <tr><td class="col data" data-th="Spur">H0</td></tr>
        </tbody></table>
        <table id="product-attribute-specs-table"><tbody>
        <tr><td class="col data" data-th="Stromsystem">DC Analog</td></tr>
        </tbody></table>
        <table id="product-attribute-specs-table"><tbody>
        <tr><td class="col data" data-th="Länge über Puffer">164 mm</td></tr>
        <tr><td class="col data" data-th="Mindestradius">358 mm</td></tr>
        </tbody></table>
        """
        specs = pdp._extract_specs_table(html)
        self.assertEqual(specs.get("Spur"), "H0")
        self.assertEqual(specs.get("Länge über Puffer"), "164 mm")
        self.assertEqual(specs.get("Mindestradius"), "358 mm")
        patch = pdp._specs_to_model_patch(specs)
        self.assertEqual(patch.get("luepMm"), 164)
        self.assertEqual(patch.get("minRadiusMm"), 358)


class TestTrimDescriptionMerge(unittest.TestCase):
    def test_preserves_newlines_collapses_spaces_per_line(self) -> None:
        self.assertEqual(
            pdp._trim_description_merge("  a  b\n  c\t\td  \n\n"),
            "a b\nc d",
        )


class TestMergeArticleRecordRobustness(unittest.TestCase):
    def test_corrupt_existing_json_raises_system_exit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "70006.json").write_text("{not-json", encoding="utf-8")
            with self.assertRaises(SystemExit) as ctx:
                pdp.merge_article_record(
                    {"articleNumber": "70006", "modelPatch": {}},
                    notes="n",
                    articles_root=root,
                    article_override=None,
                    merge_only=None,
                )
            self.assertIn("gültiges JSON", str(ctx.exception))

    def test_modelpatch_electric_system_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "70007.json"
            base = pdp.article_record_stub("70007")
            base["model"]["electricSystem"] = "dc"
            path.write_text(
                json.dumps(base, ensure_ascii=False),
                encoding="utf-8",
            )
            merged, _ = pdp.merge_article_record(
                {
                    "articleNumber": "70007",
                    "modelPatch": {"electricSystem": "völlig unklar"},
                },
                notes="n",
                articles_root=root,
                article_override=None,
                merge_only={"model.electricSystem"},
            )
            self.assertIsNone(merged["model"]["electricSystem"])


class TestProductImageUrl(unittest.TestCase):
    def test_data_src_main_image(self) -> None:
        base = "https://www.roco.cc/foo/bar-70002.html"
        html = (
            '<html><body>'
            '<img id="img" class="main-image" data-src="/responsebinary.php?x=1" />'
            "</body></html>"
        )
        u = pdp._product_image_url(html, base)
        self.assertTrue(u)
        self.assertIn("responsebinary.php", u)


if __name__ == "__main__":
    unittest.main()
