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
            )
            self.assertEqual(merged["source"]["imageUrl"], "https://cdn.example/new.png")


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
