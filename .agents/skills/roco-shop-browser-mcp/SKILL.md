# Roco Shop über Chrome DevTools MCP (Primär)

Nutze diese Skill, wenn der User **Roco-Produktdaten direkt von roco.cc** beziehen will (Magento-Shop), **ohne** parallelen HTTP‑Scraper zur PDP (kein `curl`, kein `roco_shop_parse_pdp.py --url` neben der Session).

**Primär:** **Chrome DevTools MCP** (`user-chrome-devtools`): echter Chrome, den du per MCP steuerst. **Vor jedem Einsatz** die Tool-Schemata unter  
`/Users/yannik/.cursor/projects/Users-yannik-Documents-Projects-locobox2-database-data/mcps/user-chrome-devtools/tools/` lesen.

**Nicht für Batch‑Scrapes:** **Cursor IDE Browser MCP** (`cursor-ide-browser`) verlangt in der Praxis oft **Bestätigung pro Aktion** und ist für viele PDP‑Zyklen ungeeignet. Nur nutzen, wenn der User das ausdrücklich will oder kein Chrome MCP verfügbar ist.

PDP‑HTML für den Parser kommt **aus derselben** Chrome‑Session (siehe Phase B).

Triggers (Beispiele): «Roco Shop mit Browser scrapen», «Produkte von der Webseite wie ein User», Start-URL zum Lok‑Listing angegeben, «Chrome MCP».

## Ziele

- Aus der Listenseite **der Reihe nach** jedes Produkt im **gleichen Tab** besuchen (Liste → PDP → zurück zur Liste → nächste PDP), Daten aus der PDP lesen und `**articles/roco/{articleNumber}.json`** **aktualisieren oder neu anlegen**.
- `**source.url`**: kanonische Produkt‑URL der Seite im Tab.
- `**source.notes`**: `Daten von der Webseite, automatisch geupdated.` (genau so, falls der User nichts anderes vorgibt).
- `**updatedAt`**: ISO‑UTC Zeitstempel nach Schreiben der Datei.

## Vorgaben vom User (immer klären oder übernehmen)

1. `**startUrl`**: komplette Listing‑URL (z. B. gefilterte Lokomotiven‑Kategorie).
2. `**listingPages`**: wie viele **Listenseiten** der Pagination insgesamt bearbeitet werden sollen (Integer ≥ 1). Nur diese Seiten durchlaufen; nicht mehr selbständig erweitern.
3. Optional: ob **nur bestehende JSON‑Dateien** ergänzt werden sollen oder auch **neue** angelegt werden (Default: wenn User nichts sagt, bestehende + neue wie vom User gewünscht formulieren).

## MCP‑Pflichtregeln (Chrome DevTools)

1. `**list_pages`** zu Beginn; Ziel‑Tab mit `**select_page`** (`pageId`) auswählen, falls mehrere Seiten offen sind.
2. `**navigate_page`** mit `type: "url"` und `url: <startUrl>` (bzw. Listing‑ oder PDP‑URL). Für «Zurück zur Liste» wieder `**navigate_page`** mit der **gespeicherten** Listing‑URL (nicht nur «back», falls Historie fehlt).
3. Vor jedem Klick: `**take_snapshot`** (liefert Elemente mit `**uid`**). Nach Navigation oder PDP‑Wechsel immer neuen Snapshot.
4. Klick: `**click`** mit `uid` aus dem **aktuellen** Snapshot.
5. Warten: `**wait_for`** mit erwartetem Seitentext (z. B. Toolbar «Artikel» oder PDP‑Titel) **oder** kurze Pause zwischen Schritten (2–5 s, leicht variieren). Keine Klick‑Salven.

**Hinweis:** Es gibt kein separates «Lock»; trotzdem **seriell** vorgehen (ein Tab, eine PDP nach der anderen).

## Realistisches Nutzerverhalten (Pflicht)

- Zwischen **Navigation**, **Klicks** und **Pagination** jeweils etwa **2–5 s** warten (leicht variieren).
- Ziel-Link im Snapshot finden; falls nötig, mit `**evaluate_script`** z. B. `() => { document.querySelector('a.product-item-link')?.scrollIntoView({block:'center'}); }` (nur wenn nötig; Rückgabe JSON‑serialisierbar halten, z. B. `true`).
- Overlays (Cookies): im Snapshot erkennen, Dialog schliessen oder Nutzer bitten.

## Ablaufstrategie (seriell, ein Tab in Chrome)

**Immer:** Liste → Artikel 1 → Liste → Artikel 2 → … (kein Mittelklick‑Sturm auf PDPs).

**Pro Listenseite** (erst wenn alle Produkte dieser Seite durch sind, Pagination wechseln):

### Phase A — Listing laden und Reihenfolge festlegen

1. `**navigate_page`** → `**startUrl`**. URL **exakt merken** für jedes «Zurück zur Liste».
2. `**take_snapshot`** → **Produkttitel‑Links** in **Rasterreihenfolge** (lesbare Namen wie «Dampflokomotive …», nicht der Bild‑Link mit CSS‑Noise «`.product-image-container-…`»). Artikelnummern aus Karten wo sichtbar.

### Phase B — Pro Artikel: Liste → PDP → JSON → Liste

Für **jedes** Produkt auf dieser Listenseite **nacheinander**:

1. Falls nicht auf der Liste: `**navigate_page`** mit gespeicherter Listing‑URL.
2. `**take_snapshot`** → `**uid`** des **Produkttitel‑Links** für das nächste unerledigte Produkt → `**click`** (`uid`).
3. `**wait_for`** / kurze Pause → `**take_snapshot`** auf PDP. Aus Snapshot: **aktuelle URL** (Adresszeile / Metadaten im Snapshot‑Output, je nach MCP‑Format) als kanonische PDP‑URL merken.
4. **HTML derselben Session** holen (kein `--url` zu roco.cc):
  - `**evaluate_script`** mit z. B.  
   `() => { return document.documentElement.outerHTML; }`  
   Rückgabe kann sehr gross sein: wenn das MCP‑Limit knapp wird, stattdessen mit demselben Script in eine Datei schreiben (z. B. über `fetch('data:...')` geht nicht zuverlässig); praktisch: Rückgabestring vom Tool in `**.tmp/roco-pdp.html`** im Repo schreiben (Ordner `.tmp/` anlegen, in `.gitignore` ist sinnvoll).
5. Parser vom Repo‑Root:
  `python3 utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py --html-file '.tmp/roco-pdp.html' --canonical-url '<PDP-URL aus Adresse/Snapshot>' --write --quiet`
   Optional `--article NR`, `--notes`, `--articles-root`. `**--canonical-url`** ist Pflicht, falls `og:url` im gespeicherten HTML fehlt oder zweifelhaft ist.
6. `**navigate_page`** zur **gespeicherten Listing‑URL** → nächstes Produkt ab Schritt 4.
7. Fehler: Listing wiederherstellen, Artikel + Grund notieren; optional `**take_screenshot`**.

### Phase C — Pagination

1. Am Ende der Karten: `**take_snapshot`** → Link «Weiter» / `p=` → `**click`** → warten → neue Listing‑URL merken → Phase A–B.
2. Bis `**listingPages`** erreicht oder keine nächste Seite → kurzes Ergebnisprotokoll.

## Hinweise Magento (roco.cc)

- Karten: `**.product-article-number`**, PDP oft unter `**a.product-item-link**`.
- Toolbar «Artikel X–Y von Z» zur Plausibilisierung.

## Skalierung

- Typisch **24** Karten pro Seite → 24 Zyklen «Liste → PDP → Liste». `**listingPages`** klein halten, wenn instabil.

## Was nicht verwendet wird

- `**utils/roco/roco_web_scrape.py`** (entfernt).
- `**roco_shop_parse_pdp.py --url`** auf roco.cc **im gleichen Workflow** wie der Browser (andere Session). `**--url`** nur für manuelle/offline Jobs ohne Shop‑Session.

## Kurz-Checkliste

- `startUrl`, `listingPages` vom User (oder Defaults klar sagen).
- **Chrome MCP:** `list_pages` → `select_page` → Listing `navigate_page` → URL speichern.
- Pro Artikel: `take_snapshot` → Titel‑`click` → PDP → `evaluate_script` → HTML‑Datei → `**roco_shop_parse_pdp.py --html-file … --canonical-url … --write`** → Listing‑`navigate_page`.
- Kein curl / kein `--url` zu roco.cc in diesem Flow.
- Pagination bis `listingPages` oder Ende.
- Kurzes Protokoll.