# Roco-Hilfsprogramme

**Abhängigkeiten:** siehe **`../requirements.txt`** und **`../README.md`** (venv, Python **3.10+** für MCP-Import und `pip install`).

| Ordner | Zweck |
|--------|--------|
| **`shop-pdp-parse/`** | PDP parsen (`roco_shop_parse_pdp.py`); optional Import über Chrome-MCP-stdio (`roco_mcp_chrome_search_import.py`, [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)). |

Alle Skripte erwarten das Repo-Root drei Ebenen über dem jeweiligen `.py`-Pfad (`parents[3]`).
