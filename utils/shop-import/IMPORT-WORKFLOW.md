# Shop-Import-Workflow (Agent + User-Terminal)

End-to-end Ablauf: vom **Roh-Input** (PDF, ungefilterte Liste) bis zum **Handoff-Block** nach dem Lauf. Der **User** führt Shell-Befehle aus; der **Agent** bereitet Listen und Copy-Paste-Blöcke vor.

## Hersteller-Allowlist (automatischer Flow)

| Hersteller | Stufe 1 (Queue) | Stufe 2 (MCP-Import) | Parser / Autofix |
|------------|-----------------|----------------------|------------------|
| **PIKO** | ja | ja | `piko_mcp_chrome_search_import.py`, `autofix_piko_shop_type.py`, … |
| **Roco** | ja (eigene Queues) | ja | `roco_mcp_chrome_search_import.py`, Roco-Autofix-Skripte |
| **Andere** | — | **nein** (noch nicht) | Vor neuer Hersteller-Integration: Workflow hier erweitern, nicht improvisieren |

Neue Hersteller = eigener Parser, MCP-Skript, Kampagnen-Tag-Konvention und Skill-Wiki. Bis dokumentiert: Agent **stoppt** nach Queue-Erstellung oder manuellem Review, kein MCP-Import.

---

## Rollen

| Phase | User | Agent |
|-------|------|-------|
| Input | PDF hochladen / Pfad nennen, oder rohe Artikelliste, optional Preisfilter | — |
| Queue | — | Katalog extrahieren oder Liste bereinigen → `.tmp/{hersteller}_…_article_numbers.txt` |
| Befehle | Copy-Paste aus Agent-Antwort ins Terminal | Konkrete Blöcke (`CAMPAIGN`, `QUEUE`, `--delay`) |
| Lauf | Import + Autofix + `npm run check` | — |
| Abschluss | Ergebnis mitteilen (Terminal-JSON, Fehler) | [AGENT-HANDOFF-TEMPLATE.md](AGENT-HANDOFF-TEMPLATE.md) ausfüllen |

---

## Workflow-Schritte

### 0. User-Input (typisch)

Eines von:

- **Katalog-PDF** (z. B. PIKO H0 Neuheiten, PIKO N Katalog)
- **Textdatei** mit Artikelnummern (noch ungefiltert, Duplikate, Kommentare ok)
- **Bestehende Queue** + «gib mir den Import-Befehl»

Optional vom User: Mindestpreis (EUR), Spur (N/H0), Kampagnen-Tag (`piko-neuheiten-2024`), Branch-Name.

### 1. Agent: Queue erstellen

**PIKO aus PDF:**

```bash
pdftotext -layout pfad/zu/katalog.pdf .tmp/piko_catalog.txt
python3 utils/piko/catalog-extract/extract_piko_h0_catalog.py \
  --text-file .tmp/piko_catalog.txt \
  --articles-queue-out .tmp/piko_shop_article_numbers.txt \
  --min-price-eur 120
```

Agent liefert:

- Pfad zur Queue-Datei
- Zeilenanzahl (SKUs)
- ggf. `.tmp/*_over_120eur.txt` / Filter-Notiz

**Aus ungefilterter Liste:** eine Nummer pro Zeile, `#` Kommentare, nur Ziffern 4–8 Stellen; Duplikate entfernen; in `.tmp/` schreiben.

**Katalog vs. Repo:** optional fehlende SKUs in `.tmp/{kampagne}_missing.txt` vormerken (nach Import abgleichen).

### 2. Agent: Import-Befehl (User kopiert)

Nur wenn Hersteller in **Allowlist** (PIKO/Roco). Siehe [README.md](README.md) → Kopierblock Shop-Import.

Beispiel PIKO:

```bash
CAMPAIGN=piko-neuheiten-2024
QUEUE=.tmp/piko_shop_article_numbers.txt

.venv/bin/python utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py \
  --articles "$QUEUE" \
  --mcp-from-cursor \
  --campaign-tag "$CAMPAIGN" \
  --delay 3.0
```

Am Ende des Laufs: Terminal-Zeile `{"ok": N, "fail": M}`.

### 3. User: Import ausführen

Voraussetzungen: venv, `chrome-devtools` in `~/.cursor/mcp.json`. User startet Befehl **selbst**, wartet auf Abschluss.

### 4. Agent: Autofix-Befehle (User kopiert)

PIKO (Scope anpassen):

```bash
SCOPE=articles/piko
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofix_piko_shop_type.py --apply "$SCOPE"
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofix_model_country.py --apply "$SCOPE"
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofill_categories_from_piko_url.py --apply "$SCOPE"
npm run check
```

Danach optional **Loknummer Pass 1** (Skill `.agents/skills/lok-numbering-article-review/`) auf Kampagnen-Tag.

### 5. Agent: Handoff-Block

Ausgefüllte Tabelle aus [AGENT-HANDOFF-TEMPLATE.md](AGENT-HANDOFF-TEMPLATE.md) — für PR, Issue oder neuen Chat.

---

## Agent-Prompts (User → Agent)

| User sagt ungefähr | Agent liefert |
|--------------------|---------------|
| «Hier PIKO-PDF, >120 EUR, Kampagne 2024» | Schritt 1 Befehle + Queue-Pfad, dann Schritt 2 Import-Block |
| «Queue liegt in `.tmp/foo.txt`, Import-Befehl bitte» | Schritt 2 (CAMPAIGN klären falls nötig) |
| «Import fertig, 240 ok 3 fail» | Schritt 4 Autofix-Block + Schritt 5 Handoff |
| «Neuer Hersteller X» | Hinweis: nicht in Allowlist → kein MCP bis Workflow erweitert |

---

## Verweise

- Befehle, MCP, Fehler: [README.md](README.md)
- Handoff-Vorlage: [AGENT-HANDOFF-TEMPLATE.md](AGENT-HANDOFF-TEMPLATE.md)
- PIKO Review nach Import: `.agents/skills/lok-numbering-article-review/`
