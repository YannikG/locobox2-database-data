# Belgien (NMBS/SNCB): Plausibilität für Locobox-Artikel

Überblick **Nationale Gesellschaft der Belgischen Eisenbahnen** / NMBS-SNCB: deutschsprachiger Wikipedia-Hauptartikel [«Nationale Gesellschaft der Belgischen Eisenbahnen»](https://de.wikipedia.org/wiki/Nationale_Gesellschaft_der_Belgischen_Eisenbahnen) (Geschichte, 3 kV, Mehrsystem, Güter **Lineas**-Umfeld). Gesamtliste der Baureihen auf dewiki oft **über Einzelartikel** «NMBS/SNCB-Reihe …» verstreut; ergänzend englische Gesamtübersicht (siehe Provenienz).

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **BE** |
| `operator` | **SNCB** / **NMBS** (Schreibweisen je Epoche; heute oft **SNCB** im internationalen Kontext); Güter **Lineas** usw. nur mit Textbeleg |
| `electricSystem` | Hauptnetz **3 kV DC**; **25 kV AC** (LGV, Hochgeschwindigkeit); **Mehrsystem**-Loks im Fliesstext prüfen |
| `categories` | Viele **elektrolokomotive** / **triebzug**; Vermietung und SNCB-Lack auf fremdem Vorbild → Operator und Epoche nicht raten |

## Split `type` / `number`

- Wie Nachbarländer oft «**13 003**»-Schreibweise oder **HLE**-Präfixe; BR in `type`, Rest in `number`, wenn der Import zweiteilig erkennbar ist.

## Grenzfälle

- **SNCB vs. SŽ / Vermieter:** `livery` oder Beschriftung «SZ» etc. mit `operator` **SNCB** → Finding, kein Auto-Fix `country` ohne Text.
- **Mehrsystem vs. Kategorie:** Widerspruch → Finding.

## Review-Hinweis

- Stromsystem vs. Baureihe; Lok vs. Triebzug → **Finding**.

## Provenienz

**Primär (Kontext, Geschichte, Technik):** https://de.wikipedia.org/wiki/Nationale_Gesellschaft_der_Belgischen_Eisenbahnen

**Ergänzend (englisch, Baureihen-Inventar):** https://en.wikipedia.org/wiki/List_of_SNCB/NMBS_classes

Inhalt dieser Datei **komprimiert offline**.
