# Skill-internes Wissen (offline, erweiterbar)

Jede Datei `wiki-*.md` ist ein **komprimiertes Referenzpaket** für Plausibilitätsreviews: Tabellen zu `country`, `operator`, Stromsystem, typische Baureihen, Kategoriechecks und Split-Hinweisen. **Nicht** als juristischer oder betrieblicher Nachweis gedacht.

**Regel:** Validierungsfakten stehen **im Markdown**; **Provenienz** steht **am Ende** der Länder-`wiki-*.md` unter «Provenienz». **Ausnahmen:** `wiki-baureihen-schemata-uebersicht.md` ist ein bewusster **Link-Index**; manche Länderdateien haben **einen** Wikipedia-Primärlink direkt unter dem Titel. Keine langen Linklisten im übrigen Fliesstext.

**Parsing:** `field-parsing-model.md` beschreibt, wie `model.type` / `model.number` gesplittet werden und wo **herstellerspezifische Variantengruppen** (Schwesterartikel für Auto-Fix) dokumentiert werden. **Schemata:** `wiki-baureihen-schemata-uebersicht.md` sammelt Wikipedia-Links zu UIC, DB, DR, Österreich, Schweiz, PKP, British Rail, RhB.

**Repo-Skripte (Python, Auto-Fix):** vom Repo-Root unter `utils/agents/lok-numbering-article-review/scripts/` (Split, optional `description`-OCR, Unit-Tests). Kommandos und Flags: `SKILL.md`, Abschnitt «Auto-Fix» und Unterabschnitt «Repo-Skripte».

**Ablauf:** Siehe `SKILL.md`: Phase 1 (voller Pass, alle Findings), Phase 2 (eine JSON pro Runde, User: `skip` / `ignore` / konkret), Schlussliste. Ignorierte Punkte erst wieder aufnehmen, wenn der User das **explizit** verlangt.

**Erweiterung:** Neue Datei als `wiki-<kurzname>.md` hier ablegen; in `SKILL.md` Tabelle «Domain-Wissen» eine Zeile ergänzen. Keine tiefe Verschachtelung (max. eine Ebene unter diesem Ordner). Beispiele: `wiki-sncf-loks-liste.md` (Frankreich), `wiki-schweden-loks-kategorien.md` (Schweden), `wiki-polen-pkp-loks-liste.md` (Polen), `wiki-daenemark-dsb-loks-liste.md` (Dänemark), `wiki-dr-reichsbahn-1920-1945-baureihen-liste.md` (DR 1920–1945), `wiki-dr-ddr-baureihen-liste.md` (DDR Deutsche Reichsbahn 1945–1993), `wiki-slowakei-zssk-loks-liste.md` (Slowakei ŽSSK), `wiki-baureihen-schemata-uebersicht.md` (Baureihen-/UIC-Schemata, Link-Index), `wiki-belgien-nmbs-loks-liste.md` (Belgien NMBS/SNCB).
