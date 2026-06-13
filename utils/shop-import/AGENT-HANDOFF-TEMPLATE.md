# Chrome headless: Agent-Rückmeldung (Pflicht)

## Rollen

| Wer | Was |
|-----|-----|
| **User** | Führt die Shell-Befehle **selbst** im Terminal aus (neben dem Agent-Chat). Katalog-PDF, Queue-`.txt` und Import laufen auf der Maschine des Users. |
| **Agent** | Liefert **fertige Copy-Paste-Blöcke** (Queue-Pfad, `--campaign-tag`, `--delay`, Autofix, `npm run check`) und am Ende den **ausgefüllten Handoff-Block** unten. Der Agent startet den Import **nicht** stellvertretend, ausser der User verlangt das ausdrücklich. |

Typischer Ablauf: Katalog analysiert → Artikelnummern-Liste liegt in `.tmp/…txt` → User fragt den Agent «gib mir den Import-Befehl» → User führt den Befehl aus → User meldet Ergebnis oder Agent liest Terminal/JSON → Agent liefert Handoff-Block für PR/neuen Chat.

Runbook (Befehle, MCP, Fehler): [README.md](README.md). Gesamtworkflow: [IMPORT-WORKFLOW.md](IMPORT-WORKFLOW.md).

---

## Vorlage (ausfüllen und zurückgeben)

```markdown
## Chrome headless Shop-Import

| Feld | Wert |
|------|------|
| **Hersteller** | PIKO \| Roco |
| **Kampagne** | `{CAMPAIGN_TAG}` |
| **Branch** | `{branch-name}` |
| **Queue-Datei** | `{path/to/queue.txt}` |
| **Queue-Grösse** | `{N}` Artikelnummern |
| **Import (MCP)** | `{OK}` ok, `{FAIL}` fehlgeschlagen |
| **JSON geschrieben** | `{COUNT}` unter `articles/{hersteller}/` |
| **Autofix** | `autofix_piko_shop_type` (+ country, categories) — {ja/nein, Anzahl geändert} |
| **`npm run check`** | {PASS \| FAIL — bei FAIL Fehlerzeile} |
| **Katalog vs. Shop** | {z. B. «112 Katalog-SKUs, 98 im Shop, 14 missing → `.tmp/…_missing.txt`»} |
| **Offene Pass-2-Findings** | {kurz oder «keine»} |
| **Commits** | {SHAs oder «noch uncommitted»} |
```

### Kurz-Checkliste (Agent, vor Rückmeldung)

- [ ] User hat Import-Befehl erhalten (Copy-Paste mit korrektem `QUEUE` + `CAMPAIGN`)
- [ ] Import-JSON `{"ok":…,"fail":…}` aus User-Terminal oder Log ausgewertet
- [ ] User hat Post-Import-Autofix-Befehle erhalten (oder selbst ausgeführt)
- [ ] `npm run check` — Ergebnis bekannt
- [ ] Fehlende Shop-SKUs: Pfad zu `.tmp/*_missing.txt` genannt (falls Katalog-Abgleich)
- [ ] Obiger Handoff-Block an User/PR gepostet

### Was der Agent dem User geben soll (Copy-Paste)

Sobald die Queue-Datei existiert, **zuerst** diese Blöcke ausgeben (Pfade/Tags konkret einsetzen, nicht Platzhalter stehen lassen):

```bash
# 1) Shop-Import — User führt diesen Befehl selbst aus
CAMPAIGN=piko-neuheiten-2024
QUEUE=.tmp/piko_shop_article_numbers.txt

.venv/bin/python utils/piko/shop-pdp-parse/piko_mcp_chrome_search_import.py \
  --articles "$QUEUE" \
  --mcp-from-cursor \
  --campaign-tag "$CAMPAIGN" \
  --delay 3.0
```

```bash
# 2) Danach Autofix + Check — ebenfalls User-Terminal
SCOPE=articles/piko
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofix_piko_shop_type.py --apply "$SCOPE"
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofix_model_country.py --apply "$SCOPE"
.venv/bin/python utils/agents/lok-numbering-article-review/scripts/autofill_categories_from_piko_url.py --apply "$SCOPE"
npm run check
```

Erst **nach** dem Lauf: Handoff-Tabelle unten ausfüllen.

---

## Beispiel (PIKO Neuheiten 2024)

```markdown
## Chrome headless Shop-Import

| Feld | Wert |
|------|------|
| **Hersteller** | PIKO |
| **Kampagne** | `piko-neuheiten-2024` |
| **Branch** | `piko-2024` |
| **Queue-Datei** | `.tmp/piko_2024_h0_over_120eur.txt` + `.tmp/piko_2024_n_over_120eur.txt` |
| **Queue-Grösse** | ~393 Katalog-SKUs (H0 + N) |
| **Import (MCP)** | 257 ok, Rest Shop nicht auffindbar |
| **JSON geschrieben** | 257 unter `articles/piko/` |
| **Autofix** | ja — electricSystem, type/country, categories; TX Logistik BR 187 Split |
| **`npm run check`** | PASS |
| **Katalog vs. Shop** | Lücken mostly shop-unavailable; Listen `.tmp/piko_2024_h0_missing.txt`, `.tmp/piko_2024_n_missing.txt` |
| **Offene Pass-2-Findings** | keine Blocker; fehlende Katalog-SKUs für Folge-PR |
| **Commits** | `4f95c41` … `2a72b93` |
```
