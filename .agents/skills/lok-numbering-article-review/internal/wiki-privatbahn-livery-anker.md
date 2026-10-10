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
| ecco-Rail / eccorail | **NL** | |
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
| EU07 + **PR** | **PL** | |
| E483 PMT | **IT** | |
| Strukton | **NL** | |
| Medway, Captrain, Northrail, Beacon, Black Dragons, WFL, Press, HSL, National Express, … | **DE** | nur bei klarem Namen im Blob |
| **USA**, **Norte**, D&RGW, Southern Pacific | **US** | |

## Operator fehlt zusätzlich

Wenn **`operator`** `null` ist, aber der Anker eindeutig ist (z. B. **DB Italia** in Livery, **DB/DR** bei Personenzug-Set im Fliesstext):

- **Finding** mit Vorschlag Operator + Land
- Auto-Fix nur gemäss `SKILL.md` und Skript-Allowlist

## Grenzen

- **MRCE / Railpool / Alpha Trains** usw. fahren international; Tabelle gilt für **Modell-Spurware** im Shop-Titel, nicht für realen Einsatzort.
- Gleiche Livery, unterschiedliche Epoche/Stromsystem: **Schwester prüfen**, nicht blind kopieren.
- Neue EVU-Namen: Zeile hier ergänzen, nicht ad hoc in Pass 1 erfinden.

## Provenienz

Locobox-Review PIKO Neuheiten 2024; konsolidiert aus wiederkehrenden `Privatbahn`-Importen und `autofix_model_country.py`-Regeln (Skript ist Implementierung, diese Datei ist **Review-Referenz**).
