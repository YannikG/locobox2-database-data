# Slowakei (ŽSSK, ZSSK Cargo, Geschichte ČSD): Plausibilität für Locobox-Artikel

**Baureihen-Gesamtliste:** deutschsprachige Wikipedia [«Liste der Lokomotiv- und Triebwagenbaureihen der ŽSSK»](https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C5%BDSSK) (siehe Provenienz). Viele Baumuster stammen aus **ČSD**-Ära oder tschechischer Produktion; Abgleich mit [wiki-tschechien-lokklassen-liste.md](wiki-tschechien-lokklassen-liste.md), **`country`** nur mit Textbeleg setzen.

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **SK** |
| `operator` | **ŽSSK** (Personenverkehr; Shop oft «ZSSK» ohne Hächen), **ZSSK Cargo** (Güter); historisch **ČSD** / grenzüberschreitend **ČD** nur wenn `description` oder URL das tragen |
| `electricSystem` | Wie Nachbarnetze: häufig **25 kV 50 Hz** und **3 kV DC**; Mehrsystemloks im Artikeltext prüfen |
| `categories` | `elektrolokomotive`, `diesellokomotive`, `triebzug` je nach Baureihe; keine Vermischung ohne Textbeleg |

## Baureihen-Stichworte (unvollständig)

- **Elektro:** **240** «Laminátka», **350** «Gorila», **362** / **363** Mehrsystem, **461** «Pantograf», moderne Mehrsystem- und Güterloks laut Originaltabelle.
- **Diesel:** **750** «Hektor», **771** u. a.; viele Nummern parallel zu tschechischen Mustern.
- **Triebwagen:** Regional- und Fern-Triebzüge gemäss ŽSSK-Liste; Epoche und Lack aus Modell-/Shop-Text.

## Split `type` / `number`

- Gleiches Muster wie in Tschechien: «**363 129-4**»-ähnliche Dreier-BR + Nummer mit Prüfziffer → Standard-Split, wenn der Import nicht schon trennt.

## Grenzfälle

- **ČD- oder MRCE-Anschriften** auf slowakischer Strecke: Operator und Epoche aus Beschreibung, nicht nur aus Baureihe.
- **ZSSK** vs **ŽSSK** in Unicode: im JSON konsistent zur Projekt-Konvention; Shop-ASCII bleibt Finding-fähig, nicht automatisch überschreiben.

## Review-Hinweis

- Stromsystem vs. Baureihe; `country` **SK** vs. **CZ** / **CS** (Historik) → bei Widerspruch **Finding**.

## Provenienz

**Primär:** deutschsprachige Wikipedia «Liste der Lokomotiv- und Triebwagenbaureihen der ŽSSK»: https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C5%BDSSK

Inhalt dieser Datei **komprimiert offline**.
