# `model.type` und `model.number`: Splitting und Lesarten

Locobox-Schema (`contracts/article.schema.json`): beide Felder sind optionale Strings. Importe liefern oft **eine** zusammengezogene Anschrift; das Review soll vorschlagen, wie man sie **sinnvoll aufteilt** oder ob **eine** Zeichenkette beibehalten werden soll.

## Ziele beim Review

1. **Parsen:** Welche Baureihe / Gattung / Reihe und welche **laufende Nummer** stecken im String?
2. **Split-Vorschlag:** Konkrete Belegung von `model.type` vs `model.number` (inkl. „nur eines befüllen“ wenn sinnvoll).
3. **Plausibilität:** Passt das zu `operator`, `country`, `description`, `source.url`, `categories`?
4. **Livery nach Split:** Enthielt der Roh-String (oder der erste Beschreibungssatz) einen **eigenständigen Namen** neben der Nummer (Taufname, Sonderfolierung, Piercer-/Marketingbezeichnung, Zug-/Produktname in typografischen Anführungszeichen)? Dann nach dem Split prüfen: liegt das sinnvoll in **`model.livery`** (kurz, suchbar), oder steckt es nur noch im Fliesstext? **Vermeiden:** generisches `SBB`/`OBB`/`VI`, wenn die Quelle eine **konkrete Folierung** nennt; **Import-Mischstrings** in `livery` (z. B. «Elektrolokomotive 370 … „…“») als Finding markieren und bereinigen.

## Häufige Muster (heuristisch, nicht normativ)

| Muster | Typische Bedeutung | Split-Idee |
|--------|-------------------|------------|
| `NNN nnn-n` oder `NNN nnn-n` mit Leerzeichen | DB-ähnlich: Baureihe, Ordnungsnummer, Prüfziffer | `type` = Baureihe (z. B. `103`), `number` = `245-3` oder komplett `103 245-3` in `type`, `number` null je nach Projekt-Konvention |
| `NN.mm` oder `NNN.mmm` (Punkt) | Österreich, Schweiz, frühe Bezeichnungen: **Reihe / Unternummer** (oft ohne führende Null bei zweiter Gruppe) | `type` = Reihe (`77`), `number` = `14` oder `014`; Punktnotation in `type` nur behalten, wenn eure Datenbank das so indexiert |
| `Re 460 003-7` (Buchstaben + Ziffern + Strich) | CH-Kurzform | `type` oft Präfix + Baureihe (`Re 460`), `number` = `003-7`; Varianten möglich |
| `193 452-0 „Schweizpiercer“` (oder Deutschlandpiercer, ähnliche Roco-XLoad-Namen) | Baureihe + EVN-Teil + **Folien-/Marketingname** | `type` `193`, `number` `452-0`, **`livery`** z. B. `Schweizpiercer` (nicht nur generisch `SBB`, wenn der Name die Lackvariante beschreibt) |
| `370 094-2 „Adriatic Express“` | Baureihe + Nummer + **Zug-/Produktname** | `type` `370`, `number` `094-2`, **`livery`** z. B. `Adriatic Express` |
| Nur Ziffern ohne Trenner (Shop-Slug) | z. B. `7714` aus URL | Mit Beschreibung zurück in `77` + `14` splitten |

## Quellen-Reihenfolge für die Zuordnung

1. Erster Satz / Nummern in `description`
2. `source.url` (Pfadsegmente enthalten oft `7714` vs `77-14`)
3. `model.operator` / `model.country`
4. `categories` (Dampf / Diesel / Elektro)
5. Passende **`internal/wiki-*.md`** im Skill-Ordner (komprimierte Länder- und Bahnfakten **ohne** Wikipedia als Pflicht-Klick)

## Beispiel `articles/roco/70077.json`

- Roh: `model.type` = `77.14`, `number` = null, `operator` = ÖBB, Text: „Dampflokomotive **77.14** … Reihe **77** … spätere **77.14** … 1922 als **629.29**“.
- Lesart: **Reihe 77**, Betriebs-/Ordnungsnummer **14** (Schreibweise 77.14 ist klassische **Punktnotation** Österreich).
- **Split-Vorschlag (sicher):** `type`: `77` (oder `Rh 77` falls ihr Präfix standardisiert), `number`: `14`. Alternativ Konvention „alles in `type`“: `77.14`, `number` null, dann konsistent in allen ÖBB-Dampf-Artikeln.
- **Nebenfelder:** `country` sollte zu ÖBB typischerweise `AT` sein (aktuell null); `livery` null, aus Text evtl. „ÖBB“ oder Epoche; `categories` könnte um `dampflokomotive` ergänzt werden (nur Hinweis, Schema erlaubt).

## Unsicherheit

Wenn Punkt **Dezimaltrenner** in einer fremden Quelle sein könnte (selten bei Loks), ohne Kontext **unklar** markieren. Bei eindeutigem Fliesstext „Reihe 77“ + „77.14“ ist die Reihen-Interpretation **sicher**.
