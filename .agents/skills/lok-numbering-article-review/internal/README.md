# Skill-internes Wissen (offline, erweiterbar)

Jede Datei `wiki-*.md` ist ein **komprimiertes Referenzpaket** für Plausibilitätsreviews: Tabellen zu `country`, `operator`, Stromsystem, typische Baureihen, Kategoriechecks und Split-Hinweisen. **Nicht** als juristischer oder betrieblicher Nachweis gedacht.

**Regel:** Validierungsfakten stehen **im Markdown**; **Provenienz** (woher die Struktur stammt) steht **nur am Ende** jeder betroffenen Datei unter «Provenienz» — **keine** Wikipedia-URLs oder Linklisten als Hauptinhalt.

**Parsing:** `field-parsing-model.md` beschreibt, wie `model.type` / `model.number` gesplittet werden.

**Ablauf:** Siehe `SKILL.md`: Phase 1 (voller Pass, alle Findings), Phase 2 (eine JSON pro Runde, User: `skip` / `ignore` / konkret), Schlussliste. Ignorierte Punkte erst wieder aufnehmen, wenn der User das **explizit** verlangt.

**Erweiterung:** Neue Datei als `wiki-<kurzname>.md` hier ablegen; in `SKILL.md` Tabelle «Domain-Wissen» eine Zeile ergänzen. Keine tiefe Verschachtelung (max. eine Ebene unter diesem Ordner). Beispiele: `wiki-sncf-loks-liste.md` (Frankreich), `wiki-schweden-loks-kategorien.md` (Schweden), `wiki-polen-pkp-loks-liste.md` (Polen), `wiki-daenemark-dsb-loks-liste.md` (Dänemark).
