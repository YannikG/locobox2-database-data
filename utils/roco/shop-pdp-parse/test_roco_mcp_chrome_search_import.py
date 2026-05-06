"""Tests für MCP-Importer-Helfer (ohne laufenden Chrome)."""

from __future__ import annotations

import unittest

import roco_mcp_chrome_search_import as imp


class TestMcpEvaluateScriptReturnText(unittest.TestCase):
    def test_strips_script_ran_prefix_and_json_fence(self) -> None:
        raw = '''Script ran on page and returned:
```json
"<!DOCTYPE html><html><body>x</body></html>"
```'''
        out = imp._mcp_evaluate_script_return_text(raw)
        self.assertTrue(out.startswith("<!DOCTYPE html>"))

    def test_fenced_html_without_json(self) -> None:
        raw = """Script ran on page and returned:
```html
<table id='product-attribute-specs-table'></table>
```"""
        out = imp._mcp_evaluate_script_return_text(raw)
        self.assertIn("product-attribute-specs-table", out)

    def test_plain_passthrough(self) -> None:
        s = "<html></html>"
        self.assertEqual(imp._mcp_evaluate_script_return_text(s), s)


if __name__ == "__main__":
    unittest.main()
