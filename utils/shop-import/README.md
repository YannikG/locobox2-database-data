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

## Headless: Cursor Agent (ohne manuelles Browser-Klicken)

Diese Pipeline ist für **Agent-Sessions** gedacht: der Agent startet Chrome über den **stdio-MCP** `chrome-devtools` (nicht Glass/`cursor-ide-browser`). Der User muss **nicht** selbst im Shop suchen.

### Voraussetzungen

1. **Python venv** im Repo-Root: `pip install -r utils/requirements.txt` (Python ≥ 3.10, Paket `mcp`).
2. **MCP-Server** `chrome-devtools` in `~/.cursor/mcp.json` mit `command`/`args` (stdio, kein `url`-Eintrag).
3. **Kein laufender Import** auf derselben Chrome-Instanz parallel (sonst MCP-Konflikte).

### Ablauf (PIKO, vollständig)

| Schritt | Werkzeug | Ausgabe |
|--------|----------|---------|
| 1. Katalog → Queue | `pdftotext` + `extract_piko_h0_catalog.py --articles-queue-out` | `.tmp/piko_*_article_numbers.txt` |
| 2. Shop-Import | `piko_mcp_chrome_search_import.py --mcp-from-cursor` | `articles/piko/{nr}.json`, HTML unter `.tmp/piko-mcp-pdp/` |
| 3. Autofix Pass 1 | siehe unten | bereinigte `model.type` / `country` / `categories` |
| 4. Qualität | `npm run check` | Schema + Index |

**Kampagnen-Tag und Erscheinungsjahr:** `--campaign-tag` setzt den Tag im Parser; `releaseDate` kommt aus dem Kampagnen-Tag (Jahr im Slug, z. B. `piko-neuheiten-2024` → `"2024"`). Alte Tags entfernen mit `--replace-tag` (mehrfach möglich).

### Kopierblock: Shop-Import (Agent)

```bash
# Repo-Root, venv aktiv
CAMPAIGN=piko-neuheiten-2024          # anpassen
QUEUE=.tmp/piko_shop_article_numbers.txt  # eine Nummer pro Zeile

.venv/bin/python utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py \
  --articles "$QUEUE" \
  --mcp-from-cursor \
  --campaign-tag "$CAMPAIGN" \
  --delay 3.0
```

**Dry-run** (nur MCP + HTML-Länge, kein JSON-Schreiben):

```bash
.venv/bin/python utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py \
  --articles "$QUEUE" \
  --mcp-from-cursor \
  --dry-run \
  --delay 2.5
```

**Ohne Cursor-MCP-Konfig:** statt `--mcp-from-cursor` Umgebung `PIKO_CHROME_MCP_STDIO_JSON='["npx","-y","chrome-devtools-mcp@latest","--isolated"]'` oder `--mcp-stdio-json pfad/zu/mcp-argv.json`.

### Kopierblock: Post-Import Autofix (PIKO)

Nach Schritt 2 auf dem importierten Scope (z. B. `articles/piko` oder nur geänderte Dateien):

```bash
SCOPE=articles/piko

.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofix_piko_shop_type.py --apply "$SCOPE"
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofix_model_country.py --apply "$SCOPE"
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofill_categories_from_piko_url.py --apply "$SCOPE"

npm run check
```

Review-Regeln und PIKO-Shop-Artefakte: Skill **`.agents/skills/lok-numbering-article-review/`** (Pass 1 Checkliste, `internal/wiki-piko-shop-parsing.md`).

### Agent-Rückmeldung (Pflicht)

Am Ende **jeder** headless Import-Session den ausgefüllten Block aus **[AGENT-HANDOFF-TEMPLATE.md](AGENT-HANDOFF-TEMPLATE.md)** an User oder PR liefern. Kurzform:

```markdown
## PIKO Shop-Import (headless)

- **Kampagne:** `{CAMPAIGN_TAG}`
- **Queue:** `{N}` Artikelnummern aus `{QUEUE_FILE}`
- **Import:** `{OK}` ok, `{FAIL}` fehlgeschlagen (MCP/Parser)
- **Autofix:** `autofix_piko_shop_type`, `autofix_model_country`, `autofill_categories_from_piko_url`
- **Check:** `npm run check` — {PASS|FAIL}
- **Offene Findings:** {kurz, z. B. Katalog-SKUs ohne Shop-Treffer, EVN-Splits für manuelles Pass 2}
- **Branch:** `{branch-name}`
```

### Typische Fehler (Agent)

| Symptom | Massnahme |
|---------|-----------|
| `error: Stdio-Kommando fehlt` | `--mcp-from-cursor` oder `PIKO_CHROME_MCP_STDIO_JSON` setzen |
| `kein PDP-Link in Trefferliste` | SKU im Shop nicht verfügbar → in `.tmp/*_missing.txt` notieren, später nachziehen |
| `HTML zu kurz` | `--delay` erhöhen (z. B. 4.0) |
| Parser exit ≠ 0 | `.tmp/piko-mcp-pdp/{nr}.html` prüfen; ggf. Einzelartikel mit `piko_shop_parse_pdp.py --html-file …` |
| `model.type` mit EVN ohne Split | `autofix_piko_shop_type.py --apply` (UIC ohne `BR`, z. B. `187 002 …` → `BR 187` / `002`) |
