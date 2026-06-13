# Chrome headless: Agent-Rückmeldung (Pflicht)

Nach **jedem** PIKO- oder Roco-Shop-Import über `*_mcp_chrome_search_import.py` mit `--mcp-from-cursor` (oder stdio-MCP) liefert der Agent **am Ende der Session** genau **einen** Block im untenstehenden Format — als Chat-Antwort, PR-Kommentar oder Issue-Update. **Nicht** weglassen, auch wenn der User nur «importieren» sagt.

Runbook (Befehle, Autofix, Fehler): [README.md](README.md) → Abschnitt **Headless: Cursor Agent**.

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

- [ ] Import-JSON am Ende mit `{"ok":…,"fail":…}` ausgewertet
- [ ] Post-Import-Autofix auf Kampagnen-Scope (`--apply`)
- [ ] `npm run check` ausgeführt
- [ ] Fehlende Shop-SKUs in `.tmp/*_missing.txt` notiert (falls Katalog-Abgleich)
- [ ] Obiger Block an User/PR gepostet

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
