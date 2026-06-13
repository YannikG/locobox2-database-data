# Shop-Import: gleiche Strategie (Roco und PIKO)

**Hinweis:** Roco-Skripte unter `utils/roco/` bleiben unverändert; PIKO ergänzt nur eigene Pfade unter `utils/piko/`.

Ziel ist **dieselbe dreistufige Pipeline**, nur Hersteller-spezifisch bei URL und HTML-Parser.

## 1. Artikel-Queue (eine Nummer pro Zeile, `#` Kommentare erlaubt)

| Hersteller | Quelle | Werkzeug |
|------------|--------|----------|
| **Roco** | manuell / eigene `.txt` | beliebige Datei für `--articles` |
| **PIKO** | Katalog-PDF → Text | `pdftotext -layout …pdf .tmp/piko_catalog.txt` dann `python3 utils/piko/catalog-extract/extract_piko_h0_catalog.py --text-file .tmp/piko_catalog.txt --articles-queue-out .tmp/piko_catalog_article_numbers.txt` |

Beide Hersteller nutzen **dieselbe Textdatei-Form** für `--articles`: eine Artikelnummer pro Zeile, `#` für Kommentare. **Roco:** `roco_mcp_chrome_search_import.py`. **PIKO:** `piko_mcp_chrome_search_import.py`.

## 2. Chrome-DevTools-MCP (stdio)

- **PIKO:** `utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py` mit **`--articles`** (Textdatei) und **`--delay`** (Sekunden, z. B. `2.5` oder `4`).
- Stdio: Umgebung **`PIKO_CHROME_MCP_STDIO_JSON`** oder `--mcp-stdio-json`, oder `--mcp-from-cursor` (gleicher `chrome-devtools`-Server wie bei Roco).
- Ablauf: Start-URL → Suche nach Artikelnummer → PDP → HTML unter **`.tmp/piko-mcp-pdp/{nr}.html`** → **`piko_shop_parse_pdp.py`**.

## 3. PDP-Parser (kein HTTP im Parser-CLI)

| Hersteller | MCP-Import (Queue = `.txt`) | Parser | Ausgabe |
|------------|-----------------------------|--------|---------|
| **Roco** | `utils/roco/shop-pdp-parse/roco_mcp_chrome_search_import.py` | `roco_shop_parse_pdp.py` | `articles/roco/{nr}.json` |
| **PIKO** | `utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py` | `piko_shop_parse_pdp.py` | `articles/piko/{nr}.json` |

**Wichtig:** `utils/piko/catalog-extract/extract_piko_h0_catalog.py` ist **nur** Stufe 1 (Katalog-PDF). Shop-Import ist **getrennt** über `--articles` (beliebige Teilmenge, z. B. aus `--articles-queue-out` oder eine handverlesene `.txt`).

## Kurzbefehle (Roco, Referenz)

```bash
python3 utils/roco/shop-pdp-parse/roco_mcp_chrome_search_import.py \
  --articles artikel.txt --mcp-from-cursor --start-url "https://www.roco.cc/"
```

## Kurzbefehle (PIKO, getrennt)

**Nur Katalog (optional Queue für später):**

```bash
pdftotext -layout pfad/zu/katalog.pdf .tmp/piko_catalog.txt
python3 utils/piko/catalog-extract/extract_piko_h0_catalog.py \
  --text-file .tmp/piko_catalog.txt \
  --articles-queue-out .tmp/piko_catalog_article_numbers.txt \
  --min-price-eur 120
```

**Nur Shop (beliebige Teilmenge, Delay wichtig):**

```bash
.venv/bin/python utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py \
  --articles .tmp/nur_diese_nummern.txt \
  --mcp-from-cursor \
  --campaign-tag piko-neuheiten-2025 \
  --replace-tag piko-neuheiten-2026 \
  --delay 3.0
```
