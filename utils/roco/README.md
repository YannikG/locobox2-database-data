# Roco-Hilfsprogramme

**Abhängigkeiten:** siehe **`../requirements.txt`** und **`../README.md`** (venv, Python **3.10+** für MCP-Import und `pip install`).

| Ordner | Zweck |
|--------|--------|
| **`shop-pdp-parse/`** | PDP parsen (`roco_shop_parse_pdp.py`); optional Import über Chrome-MCP-stdio (`roco_mcp_chrome_search_import.py`, [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)). Derselbe `--merge-config` / `--merge-only` wie beim Parser gilt für den Importer. Presets: `merge-pdp-specs-fields.json` (Spez-Tabelle); `merge-pdp-specs-with-title-model.json` erweitert `mergeOnly` um `model.type` / `model.number` (Titel aus `og:title`). Eigene JSON nach demselben Muster möglich. **`roco_catalogue_stub.py`:** aus einer Nummernliste **nur fehlende** `articles/roco/{nr}.json` als Stub (Duplikate in der Datei entfallen; optional ``--fail-if-nothing-created``, ``--dry-run``). |

Alle Skripte erwarten das Repo-Root drei Ebenen über dem jeweiligen `.py`-Pfad (`parents[3]`).
