# Bulgarien (BDZ / Privat): Plausibilität für Locobox-Artikel

Kontext **Български държавни железници** (**BDZ** / **BDŽ**): deutschsprachiger Einstieg [«Bulgarische Staatseisenbahnen»](https://de.wikipedia.org/wiki/Bulgarische_Staatseisenbahnen) (siehe Provenienz). Keine vollständige Locobox-Baureihenliste; Review über Shoptext, EVN und Nachbarnetz RO/GR/TR. Häufiger Importkontext neben CFR: **Amintiri Feroviare / AF Models** → [wiki-amintiri-feroviare-shop-parsing.md](wiki-amintiri-feroviare-shop-parsing.md).

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **BG** |
| `operator` | **BDZ** (Personen/historisch), **BDZ Cargo** (Güter); Privat / Tochter nur bei Text (**Bulmarket**, **DB Cargo Bulgaria**, …) |
| `electricSystem` | Vorbild oft **25 kV 50 Hz AC**; Modell-H0 weiterhin `DC-Analog` / `DC-Digital` |
| `categories` | Lok vs. Wagen; BDZ-Personenwagen-Sets → `personenwagen` |

## Operator-Anker

| Text / Shop | Locobox `operator` | `country` |
|-------------|--------------------|-----------|
| BDZ, BDŽ, Bulgarian State Railways | **BDZ** | BG |
| BDZ Cargo | **BDZ Cargo** | BG |
| Bulmarket | **Bulmarket** | BG |
| DB Cargo Bulgaria | **DB Cargo Bulgaria** | BG |
| EA 3000 / Serie 86 bei DB Cargo Bulgaria | Operator laut Text, oft **DB Cargo Bulgaria** | BG |

## Baureihen-Stichworte (unvollständig)

- **Elektro:** Reihe / Klasse **46** (Shop «Reihe 46», EVN oft `91 52 0046 …`); **EA 3000** / Baureihe **86** (Skoda-Linie, auch als Dummy ohne Antrieb).
- **Diesel / Übriges:** nur mit Textbeleg; nicht aus RO-Klassen (60/62) ableiten.
- **Wagen:** BDZ-Personenwagen-Sets, offene **Eaos**-Sets (BDZ / Bulmarket) in AF-Katalogen.

## Split `type` / `number`

- «**Reihe 46**» + EVN → `type` **`Reihe 46`** oder **`46`**, Lauf-/EVN-Teil in `number`.
- «**EA 3000**» / «**86 018**» → `type` **`EA-3000`**, `number` **`86 018`** (oder vollständige EVN), wenn eindeutig.
- Dummy-/Antriebslos-Hinweis → kurz in `livery` oder `notes`, nicht den Typ verwässern.

## Grenzfälle

- **RO-Lack auf BG-Netz** oder umgekehrt: `country` nach **Betreiber** im Text, nicht nach Hersteller AF (Rumänien).
- **DB Cargo Bulgaria** vs. **DB Cargo** (DE/RO): voller Name behalten, `country` **BG**.
- Epoche fehlt → `Unbekannt`, nicht «modern = VI» raten.

## Review-Hinweis

- `country` **RO** bei BDZ-/Bulmarket-Artikel → Finding.
- Kategorie `elektrolokomotive` bei reinem Güterwagen-Set → Finding.

## Provenienz

**Primär:** https://de.wikipedia.org/wiki/Bulgarische_Staatseisenbahnen

**Ergänzend (englisch, Übersicht):** https://en.wikipedia.org/wiki/Bulgarian_State_Railways

**Nachbar RO / Shop AF:** [wiki-rumaenien-loks-liste.md](wiki-rumaenien-loks-liste.md), [wiki-amintiri-feroviare-shop-parsing.md](wiki-amintiri-feroviare-shop-parsing.md)

Inhalt dieser Datei **komprimiert offline**.
