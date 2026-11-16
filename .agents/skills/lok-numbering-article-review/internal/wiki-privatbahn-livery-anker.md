# Privatbahn-Platzhalter: Livery- und Textanker → `model.country`

PIKO (und teils andere Shops) setzen **`model.operator`: «Privatbahn»**, obwohl im Titel oder in **`model.livery`** der **Mieter / Lackierer / EVU-Name** steht. Für **Plausibilität** und konservatives **`model.country`**-Review: nur bei **eindeutigem** Anker in Livery, `model.type`, erster Beschreibungszeile oder `source.url`.

**Nicht** raten bei generischen Marketingnamen, fehlender Livery oder widersprüchlichem Fliesstext → **Finding** «Privatbahn, Land unklar».

## Anker-Tabelle (Review und Auto-Fix-Referenz)

| Anker (Livery / Typ / Fliesstext, case-insensitive) | Typisches `country` | Anmerkung |
|------------------------------------------------------|---------------------|-----------|
| Kombirail | **BE** | Belgien |
| Regiojet | **CZ** | |
| Railpool | **DE** | Vermietung, Modell oft DE-Kontext |
| MRCE | **DE** | |
| ecco-Rail / Ecco Rail / eccorail | **NL** | Operator und Livery oft **Ecco Rail** (nicht Shop-Platzhalter «EINSTELLER»/«Privatbahn») |
| Lokotrans | **CZ** | |
| RailAdventure | **CH** | |
| Train Charter | **CH** | |
| Lokaltog | **DK** | |
| Bayernbahn | **DE** | |
| Solvay | **BE** | |
| Lineas (NL) | **BE** | Lineas NL im Text |
| MKB | **DE** | |
| BLS (als Livery/EVU, nicht nur Kategorie) | **CH** | Kontext prüfen |
| RBH, IRP, SKL | **DE** | |
| Altmark-Rail | **DE** | |
| Bundeswehr (Livery) | **DE** | |
| Talent 2 (Livery/Kontext DB) | **DE** | |
| GTW 2/6 + **StB** im Fliesstext | **AT** | Stern & Hafferl / StB |
| GTW 2/6 + **HLB** | **DE** | Hessische Landesbahn |
| THURBO (Livery) | **CH** | oft mit SBB-Operator |
| DB Italia / 191 Italia | **IT** | Operator oft **DB Italia**; fehlender Operator → Finding |
| EN 57 + **PR** / **KM** im Typ | **PL** | PKP-Kontext |
| ET 21 + **CTL** | **PL** | |
| EU07 + **PR** / **EU43** | **PL** | PKP-/PL-Kontext |
| **ACTS** (Livery/Typ) | **NL** | Operator oft **ACTS** statt «Privatbahn» |
| **R-Net** / **QBuzz** | **NL** | GTW-Kontext; Operator **QBuzz** |
| **GySEV** / **Gysev** | **HU** | Operator **GySEV** |
| **EP Cargo** | **CZ** | tschechisches EVU; nicht DE |
| **Green Cargo DK** / dänische BR 5400 Green Cargo | **DK** | Operator **Green Cargo**; «DK» im Livery ist Landesmarker |
| **InRail** | **IT** | Vectron/BR 191 |
| **EVM Rail** | **IT** | Vectron E.191 |
| **PCC Intermodal** | **PL** | BR 186 / Traxx |
| **Nordwestbahn** | **DE** | BR 440 |
| **Trilex** | **DE** | Desiro |
| **WFL** | **DE** | oft im Fliesstext/Set-Titel |
| **NIS** / **D-NIS** / LOK 1 (G6) | **DE** | oft nur auf Druck, Shop-Text «Privatbahn»; Expert Plus Digitalkupplung |
| **Przewozy Regionalne** / **PR** + EU43 | **PL** | Operator **PR** oder **Przewozy Regionalne** |
| **Medway** (italienisch / E.494 / BR 186 Medway) | **IT** | FS-Klasse E.494; **nicht** pauschal DE |
| E483 PMT | **IT** | |
| Strukton | **NL** | |
| Captrain, Northrail, Beacon, Black Dragons, Press, HSL, National Express, … | **DE** | nur bei klarem Namen im Blob |
| **USA**, **Norte**, D&RGW, Southern Pacific | **US** | |

## Operator fehlt oder «Privatbahn»

Wenn **`operator`** `null` oder **«Privatbahn»** ist, aber der Anker eindeutig ist (z. B. **Medway**, **EP Cargo**, **ACTS**, **DB Italia**):

- Operator auf den **konkreten EVU-/Lacknamen** setzen
- `country` nach Anker-Tabelle; widersprüchliches Shop-`DE` korrigieren
- Auto-Fix nur gemäss `SKILL.md` und Skript-Allowlist; neue Anker zuerst hier dokumentieren

## Grenzen

- **MRCE / Railpool / Alpha Trains** usw. fahren international; Tabelle gilt für **Modell-Spurware** im Shop-Titel, nicht für realen Einsatzort.
- Gleiche Livery, unterschiedliche Epoche/Stromsystem: **Schwester prüfen**, nicht blind kopieren.
- Neue EVU-Namen: Zeile hier ergänzen, nicht ad hoc in Pass 1 erfinden.

## Provenienz

Locobox-Review PIKO Neuheiten 2024; konsolidiert aus wiederkehrenden `Privatbahn`-Importen und `autofix_model_country.py`-Regeln (Skript ist Implementierung, diese Datei ist **Review-Referenz**).
