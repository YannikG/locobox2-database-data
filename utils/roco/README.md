# Roco-Hilfsprogramme

**Abhängigkeiten:** [`../requirements.txt`](../requirements.txt) und [`../README.md`](../README.md) (venv, Python **3.10+** für MCP-Import und `pip install`).

## `shop-pdp-parse/`

- **`roco_shop_parse_pdp.py`:** PDP parsen und JSON mergen.
- **`roco_mcp_chrome_search_import.py`:** optionaler Import über Chrome-MCP-stdio ([MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)); gleiche Merge-Optionen wie beim Parser (`--merge-config`, `--merge-only`). Presets: `merge-pdp-specs-fields.json` (Spezifikationstabelle); `merge-pdp-specs-with-title-model.json` erweitert `mergeOnly` um `model.type` / `model.number` (Titel aus `og:title`). Eigene JSON-Dateien nach demselben Muster möglich.
- **`roco_catalogue_stub.py`:** aus einer Nummernliste **nur fehlende** `articles/roco/{nr}.json` als Stub anlegen (Duplikate in der Liste werden ignoriert; optional `--fail-if-nothing-created`, `--dry-run`).

Skripte gehen vom **Repository-Root** aus (Pfade relativ zum Repo).
