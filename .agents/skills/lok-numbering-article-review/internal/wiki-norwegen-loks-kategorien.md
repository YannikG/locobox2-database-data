# Norwegen: Plausibilität für Locobox-Artikel (Lokomotiven)

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **NO** |
| `operator` | **Vy** (Personen, früher Marken **NSB**), **CargoNet** (Güter), **Flytoget** (Flughafen-express, eigenes System), **Norsk Transport** historisch |
| `electricSystem` | **15 kV 16,7 Hz AC** üblich; Mehrsystem für Grenze SE/DK/FI im Text prüfen |
| `categories` | Viele **elektrolokomotive**; **diesellokomotive** El14-Nachfolger und CargoNet-Diesel; Dampf Museum |

## Antriebs-Überblick (Stichworte)

| Antrieb | Baureihen / Familien (unvollständig) |
|---------|--------------------------------------|
| Elektrolok | **El 12**, **El 13**, **El 14**, **El 16**, **El 18**; Güter moderne **Traxx**-Derivate unter **CargoNet** |
| Diesel-elektrisch | **Di 3**, **Di 4**, **Di 8** (grobe Einordnung) |
| Diesellok | Rangier und ältere Streckendiesel; **CD 66** «Euro»-Umfeld bei CargoNet |
| Dampf | Museumsbetrieb, **2’C’**- und Schmalspur-Sonderfälle |
| Normalspur | Meiste H0-Modelle; Schmalspur separat |

## Operator-Historie

- **NSB (1883–1996)** und modernere **Norwegian State Railways locomotives** im Sammler-Modell oft gemischt beschriftet → Epoche (`era`) und Fliesstext.

## Split `type` / `number`

- Nummern oft «**El 16 2217**» oder verkürzt; Buchstaben-Präfix in `type`, Ziffern in `number`, wenn sinnvoll trennbar.

## Grenzfälle

- **CargoNet** dunkles Design vs. **Vy**-Personenfarben; Verwechslung im `livery` → Finding.
- **Grenze Schweden:** IORE und Erzzug-Themen; `country` an Text koppeln.

## Review-Hinweis

- Elektro-Kategorie mit Diesel-BR oder Stromsystem ohne 15 kV im Text → **Finding**.

## Provenienz

Kategorienbaum «Locomotives of Norway» (englische Wikipedia) diente als Checkliste (Diesel / Diesel-elektrisch / Elektro / Dampf / Normalspur / NSB / CargoNet / Norsk Transport); Inhalt hier **komprimiert offline**.
