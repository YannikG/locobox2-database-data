# Dänemark (DSB, Arriva DK, …): Plausibilität für Locobox-Artikel

Gesamtübersicht **Lokomotiven und Triebwagen der Danske Statsbaner**: deutschsprachige Wikipedia [«Liste von Lokomotiven und Triebwagen der Danske Statsbaner»](https://de.wikipedia.org/wiki/Liste_von_Lokomotiven_und_Triebwagen_der_Danske_Statsbaner) (siehe Provenienz).

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **DK** |
| `operator` | **DSB** dominant; Regional **Arriva** (historisch), **Nordjyske Jernbaner**; Güter **DB Cargo Scandinavia** etc. je nach Text |
| `electricSystem` | **25 kV AC** (Hochgeschwindigkeit und viele Neubaustrecken); ältere S-Bahn **1650 V DC** («S-tog»-Umfeld) im Modelltext prüfen |
| `categories` | Viele **triebzug** (IC3, IR4, Lint, Flirt); Loks **EA**, **ME**, **MZ**-Familien |

## Baureihen-Stichworte (unvollständig)

- **Diesel:** **MY**, **MX**, **MZ**, **ME** (NOHAB und Nachfolger), Rangier **Frichs**-Umfeld (Museum).
- **Elektro:** **EA** (Co-Co), **EG** (Güter), **EB** neuere Personenzüge.
- **Triebzüge:** **IC3**, **IR4**, **IC4** (Stabilität Epoche beachten), **Lint**, **Flirt**; **S-tog** nur Grossraum **Kopenhagen** (nicht mit landesweitem IC verwechseln).

## S-tog (Spezialfall)

- Eigene **Spannung** und Betrieb; Modelltext «S-Bahn», «Flintholm», «650 V» o. ä. lesen.
- `categories` oft `triebzug`, nicht Lok.

## Split `type` / `number`

- Dänische Schreibweise «**ME 1534**» oder «**EA 3010**»; Standard-Split wenn zweiteiliger String.

## Review-Hinweis

- S-tog vs. Fern-EMU; 25 kV vs. 1650 V DC Widerspruch → **Finding**.

## Provenienz

**Primär:** deutschsprachige Wikipedia «Liste von Lokomotiven und Triebwagen der Danske Statsbaner»: https://de.wikipedia.org/wiki/Liste_von_Lokomotiven_und_Triebwagen_der_Danske_Statsbaner

**Hinweis:** Früher Bezug auf die englischsprachige DSB-Liste; massgeblich ist die **deutschsprachige** Gesamtliste (Link oben).

Inhalt dieser Datei **komprimiert offline**.
