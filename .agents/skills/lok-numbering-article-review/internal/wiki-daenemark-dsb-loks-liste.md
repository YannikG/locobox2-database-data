# Dänemark (DSB, Arriva DK, …): Plausibilität für Locobox-Artikel

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

Kompakt aus der englischsprachigen Wikipedia-Liste «List of DSB locomotives and multiple units» (Dampf / Diesel / Elektro / DMU / EMU / S-trains).
