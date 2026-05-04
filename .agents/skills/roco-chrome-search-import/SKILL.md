# Roco Artikel per Suche (Chrome DevTools MCP) → JSON

Nutze diese Skill, wenn der User **eine Liste von Artikelnummern** auf **roco.cc** abarbeiten will: **Suche** im Shop (Feld **`#search`** / **`name=q`**, Form **`#search_mini_form_0`**, Placeholder «Suchen», **`maxlength=24`**), dann **PDP‑HTML aus derselben Chrome‑Session** und Merge mit **`utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py`** (`--html-file` + **`--canonical-url`**). **Kein** `curl` und **kein** `roco_shop_parse_pdp.py --url` zu roco.cc (andere Session).

**Wichtig:** Für diesen Ablauf immer die **Shop‑Startseite** (Home) als Bezugspunkt nutzen, **nicht** eine **Listenseite** (keine gefilterte Kategorie‑URL mit Kartenraster). Die Kopfzeilen‑Suche ist dort zuverlässig; nach jedem Artikel zurück auf genau diese **Start‑URL**, nicht auf ein Lok‑Listing.

Triggers (Beispiele): «Roco Artikel per Suche importieren», «Chrome MCP Suche roco», Liste Artikelnummern durchsuchen und JSON updaten.

## Voraussetzungen

- **Chrome DevTools MCP** (`user-chrome-devtools`) ist aktiv; Tab zeigt **roco.cc** (oder zuerst dorthin navigieren).
- Vor jedem ersten Einsatz die Tool-Schemata lesen unter:  
  `/Users/yannik/.cursor/projects/Users-yannik-Documents-Projects-locobox2-database-data/mcps/user-chrome-devtools/tools/`
- Repo-Root: Artikel landen unter **`articles/roco/{articleNumber}.json`**.

## Vom User klären oder übernehmen

1. **Artikelliste**: eine Artikelnummer pro Zeile (Dateipfad) oder explizite Liste im Chat.
2. **Start‑URL**: **nur** die **Shop‑Startseite** (z. B. `https://www.roco.cc/` oder deine übliche Einstiegs‑URL wie `https://www.roco.cc/rde/` **ohne** Kategorie‑ oder Listenpfad). **Keine** Lokomotiven‑/Filter‑Listenseite als «Basis» verwenden. Wenn der User nichts angibt: **`https://www.roco.cc/`** (bzw. gleichwertige Startseite) annehmen und **exakt** für jedes Zurücksetzen vor dem nächsten `ART` merken.
3. **`--notes`** für `source.notes` (Default im Parser: `Daten von der Webseite, automatisch geupdated.`).

## MCP‑Werkzeuge (Chrome)

Typische Reihenfolge: **`list_pages`** → **`select_page`** (`pageId`) → **`navigate_page`** (`type: "url"`, **`url` = gespeicherte Startseite**) → **`take_snapshot`** → **`fill`** / **`type_text`** auf Suchfeld‑**`uid`** → **`press_key`** (Enter) **oder** **`click`** auf Lupe‑Button‑**`uid`** → **`wait_for`** mit erwartetem Text (Artikelnummer oder PDP‑Titel) → erneut **`take_snapshot`**.

Für grosse Seiten: bei Bedarf **`evaluate_script`**, um ein Element in den sichtbaren Bereich zu scrollen (Rückgabe JSON‑serialisierbar, z. B. `true`).

## Ablauf pro Artikelnummer (seriell)

Für **jede** Nummer `ART` der Liste, nacheinander:

1. **Seite bereit:** Falls nicht schon dort: **`navigate_page`** zur **Start‑URL** (Home). Dann **`take_snapshot`**. Suchfeld finden (`#search`, Rolle combobox, Placeholder «Suchen»); **`uid`** merken.
2. **Feld leeren und `ART` eintragen:** **`fill`** oder **`type_text`** mit dem **`uid`** des Inputs (nur Ziffern; Länge ≤ 24).
3. **Suche auslösen:** Enter (**`press_key`**) oder Klick auf die Lupe (**`click`** mit passendem **`uid`** aus frischem Snapshot).
4. **Warten:** **`wait_for`** (z. B. Fragment von `ART` oder PDP‑Inhalt) oder 2–5 s Pause; danach **`take_snapshot`**.
5. **Trefferlage:**
   - **Direkt PDP** (URL enthält typisch `/ART-…html` oder nur ein relevanter Treffer): aktuelle URL aus Snapshot/Adresskontext als **`CANON`** notieren.
   - **Trefferliste:** den Link zur passenden PDP (Artikelnummer / Titel) per **`click`** öffnen → wieder warten → Snapshot → **`CANON`** aus PDP.
   - **Kein Treffer:** notieren (`ART` → kein Produkt), **kein** Parserlauf mit erfundener URL.
6. **HTML derselben Session:** **`evaluate_script`** z. B.  
   `() => document.documentElement.outerHTML`  
   Rückgabe in **`.tmp/roco-pdp-{ART}.html`** schreiben (Ordner `.tmp/` anlegen; in `.gitignore` sinnvoll). Wenn die Rückgabe zu gross für eine MCP‑Antwort ist: Nutzer informieren oder **Netzwerk‑Response** des Hauptdokuments nutzen, falls dein Setup **`get_network_request`** mit Response‑Body unterstützt.
7. **Parser (Repo‑Root):**

   ```bash
   python3 utils/roco/shop-pdp-parse/roco_shop_parse_pdp.py \
     --html-file ".tmp/roco-pdp-{ART}.html" \
     --canonical-url "$CANON" \
     --write --quiet
   ```

   Optional **`--article ART`**, falls `CANON` oder `og:url` im HTML nicht zuverlässig ist.

8. **Nächster Artikel:** immer **`navigate_page`** zur **gespeicherten Start‑URL** (Home), **nicht** zur Listenseite eines Katalogs. Danach Schritt 1 (Suchfeld frisch auf der Startseite). Optional zusätzlich Suchfeld leeren, falls die Oberfläche den Query‑Text behält.

Zwischen Schritten **2–5 s** leicht variieren (menschlich).

## Harte Regeln

- **Startseite only:** keine Kategorie‑/Listenseite als Navigationsziel für Suche oder Reset.
- **Niemals** `roco_shop_parse_pdp.py --url 'https://www.roco.cc/…'` für diese Aufgabe.
- **Niemals** `curl`/wget zu roco.cc für PDP‑HTML.
- **`take_snapshot`** vor jedem **`click`**: **`uid`** immer aus dem **letzten** Snapshot.
- Cookies/Overlays: im Snapshot erkennen, schliessen oder Nutzer bitten.

## Ende

Kurzprotokoll: wie viele JSON geschrieben, welche `ART` übersprungen/fehlgeschlagen.

## Optional: gleicher Ablauf ohne Agent (weniger Tokens)

Repo-Skript **`utils/roco/shop-pdp-parse/roco_mcp_chrome_search_import.py`**: nutzt den offiziellen **[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)**-Client (`stdio_client`, `ClientSession`), startet den **Chrome-DevTools-MCP** als Subprozess (JSON-Array wie `[\"npx\", …]` in einer Datei oder in `ROCO_CHROME_MCP_STDIO_JSON`), führt Suche und `evaluate_script` aus und ruft danach **`roco_shop_parse_pdp.py`** mit `--html-file` + `--canonical-url` auf. **Python mindestens 3.10** (PyPI-Paket `mcp`); z. B. `python3.12 -m pip install --user "mcp>=1.0"` und das Skript mit derselben `python3.12` starten. Wie bei Schritt 6 oben liefert das Skript zusätzlich **`og:image` aus dem live DOM** (und optional `list_network_requests` für Katalog-Bilder) als **`--image-url`**, damit `source.imageUrl` nicht am serialisierten `outerHTML` hängen bleibt. **Dieser Skill** bleibt für manuelle oder Agent-gestützte MCP-Schritte in Cursor gültig; das Skript ist eine parallele Automatisierung.

## Verwandte Skills

- **`roco-shop-browser-mcp`**: Listings seriell im Browser; primär Chrome MCP, IDE‑Browser nur Fallback.
