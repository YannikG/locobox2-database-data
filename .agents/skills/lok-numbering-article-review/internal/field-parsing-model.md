# `model.type` und `model.number`: Splitting und Lesarten

Locobox-Schema (`contracts/article.schema.json`): `model.type` und `model.number` sind optional (Strings oder `null`). `model.electricSystem` muss, wenn gesetzt, einem der Enum-Werte entsprechen: **`DC-Analog`**, **`DC-Digital`**, **`AC-Analog`**, **`AC-Digital`** (ältere Importe oder Parserreste abweichend → **Finding**). Importe liefern oft **eine** zusammengezogene Anschrift; das Review soll vorschlagen, wie man sie **sinnvoll aufteilt** oder ob **eine** Zeichenkette beibehalten werden soll.

## Modell-Stromsystem (`model.electricSystem`) vs. Vorbild-Netz

**Locobox-Feld `model.electricSystem` beschreibt das Modell-Antriebssystem am Gleis**, nicht das Prototyp-Bahnstromnetz (15 kV 16,7 Hz, 3 kV DC, …). Die **`internal/wiki-*.md`**-Tabellen zu kV/Hz dienen dem **Vorbild-Plausibilitätscheck** in Fliesstext und Historie, **nicht** der direkten Befüllung von `model.electricSystem`.

| Shop-/Import-Hinweis (PIKO typisch) | Locobox-Wert | Review-Hinweis |
|-------------------------------------|--------------|----------------|
| `Stromsystem: Gleichstrom`, kein Werkdecoder / «nachrüstbar» | **DC-Analog** | PluX/Next18-Schnittstelle allein ≠ Digital |
| `Stromsystem: Gleichstrom` + Werk-Sound/Decoder (`Sound ja/nein: ja`, `Verbauter Decoder:`) | **DC-Digital** | Sound-Titel allein reicht nicht ohne Beleg in Attributen |
| `Stromsystem: Wechselstrom` (+ ggf. Werkdecoder) | **AC-Analog** / **AC-Digital** | analog zu Gleichstrom-Logik |
| **Keine** `Stromsystem:`-Zeile (häufig **PIKO N**) | Default **DC-Analog**; Sound werkseitig → **DC-Digital** | siehe [wiki-piko-shop-parsing.md](wiki-piko-shop-parsing.md) |

**Auto-Fix:** `model.electricSystem` wird im Skill **nicht** aus Schwesterlogik gesetzt. Parser-/Import-Pipeline darf PIKO-N-Defaults setzen; Review prüft **`null`** und Widerspruch zur Beschreibung. Details: `SKILL.md` → Allowlist Stromsystem.

## Sets und Triebzüge ohne Betriebsnummer

Langer `model.type`, **`model.number`: `null`**, **ohne** splittbare UIC/EVN in URL oder erster Beschreibungszeile — oft **kein Fehler**, sondern Set-/Triebzug-Konvention:

| Muster (nach Bereinigung Shop-Artefakte) | Split-Lesart | Finding nur wenn … |
|------------------------------------------|--------------|---------------------|
| `Schienenbus 798 mit Steuerwagen 998.6` | `type` `Schienenbus 798`, `number` `998.6` (Steuerwagen-Klasse) oder alles in `type`, `number` null | Widerspruch zwischen Titel und Beschreibung |
| `Rbe 4/4` + Set-Hinweis («2er Set», «+ Bt Steuerwagen») | `type` `Rbe 4/4`, Livery kurz Set-Bezeichnung | EVN in URL erwartet aber fehlend |
| `BR 193` / Vectron ohne Ziffernblock im Shop-Titel | `type` `BR 193`, `number` null | UIC im Fliesstext vorhanden, aber nicht gesplittet |
| `GTW 2/6` + `"Stadler"` + EVU/Lack (THURBO, HLB, …) | `type` `GTW 2/6`, Livery = Lack/EVU-Name | Livery fälschlich «Stadler» (Hersteller) |

## PIKO Variantengruppen (Schwester-Review)

Ohne Auto-Fix-Scope-Erweiterung: in **Pass 1** Stromsystem und Typ **gegen nahe Artikelnummern** vergleichen, wenn dokumentiert:

| Gruppe | Erkennung | Review |
|--------|-----------|--------|
| Sound vs. Analog | Gleiche Baureihe, benachbarte SKU; Titel «Sound-» / «inkl. Sound» | Sound-Variante → **DC-Digital** wenn Werkdecoder in Attributen; Schwester ohne Sound → **DC-Analog** |
| Gleichstrom vs. Wechselstrom | Titel «Wechselstromversion»; Paare wie Re 4/4 gleiche Lackierung | `electricSystem` AC vs. DC konsistent zum Titel |
| GTW 2/6 Stadler | Mehrere Lacks (THURBO, HLB, StB, DB …) | Livery unterscheidet; **nicht** Operator/Land von einer Variante auf andere kopieren |

Referenz Shop-Titel: [wiki-piko-shop-parsing.md](wiki-piko-shop-parsing.md). Privatbahn-Lack: [wiki-privatbahn-livery-anker.md](wiki-privatbahn-livery-anker.md).

## Ziele beim Review

1. **Parsen:** Welche Baureihe / Gattung / Reihe und welche **laufende Nummer** stecken im String?
2. **Split-Vorschlag:** Konkrete Belegung von `model.type` vs `model.number` (inkl. „nur eines befüllen“ wenn sinnvoll).
3. **Plausibilität:** Passt das zu `operator`, `country`, `description`, `source.url`, `categories`?
4. **Livery nach Split:** Enthielt der Roh-String (oder der erste Beschreibungssatz) einen **eigenständigen Namen** neben der Nummer (Taufname, Sonderfolierung, Piercer-/Marketingbezeichnung, Zug-/Produktname in typografischen Anführungszeichen)? Dann nach dem Split prüfen: liegt das sinnvoll in **`model.livery`** (kurz, suchbar), oder steckt es nur noch im Fliesstext? **Vermeiden:** generisches `SBB`/`OBB`/`VI`, wenn die Quelle eine **konkrete Folierung** nennt; **Import-Mischstrings** in `livery` (z. B. «Elektrolokomotive 370 … „…“») als Finding markieren und bereinigen.

## Häufige Muster (heuristisch, nicht normativ)

| Muster | Typische Bedeutung | Split-Idee |
|--------|-------------------|------------|
| `NNN nnn-n` oder `NNN nnn-n` mit Leerzeichen | DB-ähnlich: Baureihe, Ordnungsnummer, Prüfziffer | `type` = Baureihe (z. B. `103`), `number` = `245-3` oder komplett `103 245-3` in `type`, `number` null je nach Projekt-Konvention |
| `NN NNNN` (zwei Ziffern, Leerzeichen, **genau** vier Ziffern; oft Dampf-Titel ohne Prüfziffer) | z. B. `38 3713`, `50 1751` | `type` = `38`, `number` = `3713` (Slug `38-3713` in der URL bestätigt); **Auto-Fix** nur wenn Allowlist in `SKILL.md` erfüllt |
| `NN.mm` oder `NNN.mmm` (Punkt) | Österreich, Schweiz, frühe Bezeichnungen: **Reihe / Unternummer** (oft ohne führende Null bei zweiter Gruppe) | `type` = Reihe (`77`), `number` = `14` oder `014`; Punktnotation in `type` nur behalten, wenn eure Datenbank das so indexiert |
| `Re 460 003-7` (Buchstaben + Ziffern + Strich) | CH-Kurzform | `type` oft Präfix + Baureihe (`Re 460`), `number` = `003-7`; Varianten möglich |
| `193 452-0 „Schweizpiercer“` (oder Deutschlandpiercer, ähnliche Shop-/Marketingnamen im Import) | Baureihe + EVN-Teil + **Folien-/Marketingname** | `type` `193`, `number` `452-0`, **`livery`** z. B. `Schweizpiercer` (nicht nur generisch `SBB`, wenn der Name die Lackvariante beschreibt) |
| `370 094-2 „Adriatic Express“` | Baureihe + Nummer + **Zug-/Produktname** | `type` `370`, `number` `094-2`, **`livery`** z. B. `Adriatic Express` |
| Nur Ziffern ohne Trenner (Shop-Slug) | z. B. `7714` aus URL | Mit Beschreibung zurück in `77` + `14` splitten |

### SNCF (`BB` / `CC` / … und Ziffernblock)

In Frankreich erscheint die übliche **Anschrift** oft als **ein** String: **Präfix** (`BB`, `CC`, `Y`, …) plus **ein Ziffernblock** (häufig fünf Stellen, z. B. `72052`). Das ist **nicht** dasselbe Muster wie DB-«Baureihe plus Prüfziffer». Zwei zulässige Projekt-Lesarten: (1) **alles in `model.type`** (z. B. `CC 72052`), **`model.number`** `null`, wenn ihr die französische Schreibweise **ohne** künstlichen Split führen wollt; (2) **`model.type`** = Präfix (`CC`), **`model.number`** = der gesamte Ziffernblock (`72052`), wenn ihr Such- und Filterlogik an DB- oder CH-Splits angleichen wollt. Eine feinere Zerlegung in «Serie 72000» und «052» nur bei **eindeutigem** Beleg in `description`, `source.url` oder [wiki-sncf-loks-liste.md](wiki-sncf-loks-liste.md), sonst **Finding**, nicht raten.

## Quellen-Reihenfolge für die Zuordnung

1. Erster Satz / Nummern in `description`
2. `source.url` (Pfadsegmente enthalten oft `7714` vs `77-14`)
3. `model.operator` / `model.country` (**DR** je nach Epoche: **1920–1945** meist **`DE`**, nicht `DD`, siehe [wiki-dr-reichsbahn-1920-1945-baureihen-liste.md](wiki-dr-reichsbahn-1920-1945-baureihen-liste.md); **DDR-Reichsbahn 1945–1993** oft **`DD`**, siehe [wiki-dr-ddr-baureihen-liste.md](wiki-dr-ddr-baureihen-liste.md); Lack-«DR» der **DB AG** nicht allein als Reichsbahn-Beweis werten)
4. `categories` (Dampf / Diesel / Elektro)
5. [wiki-baureihen-schemata-uebersicht.md](wiki-baureihen-schemata-uebersicht.md) bei Zweifeln an **Baureihen-, Reihen- oder UIC-Logik** (überregional und nach Staatsbahn)
6. Passende **`internal/wiki-*.md`** im Skill-Ordner (komprimierte Länder- und Bahnfakten **ohne** Wikipedia als Pflicht-Klick)

## Hersteller und Variantengruppen (Auto-Fix)

**Schwesterartikel** gelten nur dann als Gruppe, wenn die Regel **hier**, in [wiki-piko-shop-parsing.md](wiki-piko-shop-parsing.md) (PIKO) oder in einem `internal/wiki-*.md` zum Hersteller steht (z. B. gleicher Nummernkern, unterschiedliche Ziffer für Analog/Digital/AC). Ohne Eintrag: kein automatisches Mitnehmen weiterer Dateien, nur Findings. **`model.electricSystem`** wird im Auto-Fix **nicht** aus Schwesterlogik gesetzt (siehe `SKILL.md` und Abschnitt «Modell-Stromsystem» oben).

## Skript-gestützter Split (Auto-Fix)

**Skripte-Ordner (Repo-Root):** `utils/agents/lok-numbering-article-review/scripts/` — dort liegen Split-, OCR- und Testskripte zu diesem Skill (siehe auch `SKILL.md` → «Auto-Fix» → «Repo-Skripte»).

Wenn der User **Auto-Fix** für `model.type` / `model.number` erlaubt, das Repo-Skript **`utils/agents/lok-numbering-article-review/scripts/autofix_model_type_number_split.py`** vom **Repo-Root** ausführen: zuerst **ohne** `--apply` (nur Ausgabe), bei passendem Ergebnis **`--apply`** mit demselben Pfad-Scope. Das Skript implementiert eine **Teilmenge** der Muster aus der Tabelle oben plus konservative Zusatzregeln (u. a. SNCF-ähnlich **`BB`/`CC` + fünf Ziffern** als Lesart «Präfix + Block» in separate Felder, sofern `model.number` noch leer); es ändert **keine** `description`. Grenz- und Sonderfälle (Triebzüge, Sets, PKP-Mischformen, Marketing in `model.type`) bleiben **Finding**, nicht raten. Details und Flag **`--include-br`:** Docstring / `python3 utils/agents/lok-numbering-article-review/scripts/autofix_model_type_number_split.py --help` sowie `SKILL.md` → Abschnitt «Mechanischer Split». Optional nur für Fliesstext-OCR in **`description`:** `utils/agents/lok-numbering-article-review/scripts/autofix_description_ocr.py` (gleiches Dry-Run-/`--apply`-Muster).

## Beispiel `articles/<hersteller>/70077.json`

- Roh: `model.type` = `77.14`, `number` = null, `operator` = ÖBB, Text: „Dampflokomotive **77.14** … Reihe **77** … spätere **77.14** … 1922 als **629.29**“.
- Lesart: **Reihe 77**, Betriebs-/Ordnungsnummer **14** (Schreibweise 77.14 ist klassische **Punktnotation** Österreich).
- **Split-Vorschlag (sicher):** `type`: `77` (oder `Rh 77` falls ihr Präfix standardisiert), `number`: `14`. Alternativ Konvention „alles in `type`“: `77.14`, `number` null, dann konsistent in allen ÖBB-Dampf-Artikeln.
- **Nebenfelder:** `country` sollte zu ÖBB typischerweise `AT` sein (aktuell null); `livery` null, aus Text evtl. „ÖBB“ oder Epoche; `categories` könnte um `dampflokomotive` ergänzt werden (nur Hinweis, Schema erlaubt).

## Unsicherheit

Wenn Punkt **Dezimaltrenner** in einer fremden Quelle sein könnte (selten bei Loks), ohne Kontext **unklar** markieren. Bei eindeutigem Fliesstext „Reihe 77“ + „77.14“ ist die Reihen-Interpretation **sicher**.
