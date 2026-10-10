# Auszug: UIC-Wagennummer (Güter- und Reisezugwagen)

Gilt für **Wagen**, nicht für Triebfahrzeug-Betriebsnummern. Zwölf Ziffern, gemeinsame „Sprache“ zwischen EVU, Infrastruktur und Behörden.

## Aufbau (12 Stellen)

| Stellen | Bedeutung |
|---------|-----------|
| 1–2 | Code für das Austauschverfahren (Spurweite, internationaler Einsatz, RIV/PPW usw.) |
| 3–4 | UIC-Ländercode (seit 2006: Registrierungsland; vorher oft Eigentumsmerkmal der Bahn) |
| 5–8 | Gattungskennzahlen (Gattungsbuchstabe + Kennbuchstaben als Zifferncode) |
| 9–11 | Ordnungsnummer (laufend innerhalb gleicher technischer Bauart) |
| 12 | Selbstkontrollziffer |

## Güterwagen: 5. Stelle = Gattungsbuchstabe (Auswahl)

| 5. Ziffer | Buchstabe | Bedeutung |
|-----------|-----------|-----------|
| 0 | T | Güterwagen mit öffnungsfähigem Dach |
| 1 | G | Gedeckter Güterwagen Regelbauart |
| 2 | H | Gedeckter Güterwagen Sonderbauart |
| 3 | K, O, R | Flachwagen Einzelradsätze Regelbauart |
| 4 | L, S | Flachwagen Einzelradsätze Sonderbauart |
| 5 | E | Offener Güterwagen Regelbauart |
| 6 | F | Offener Güterwagen Sonderbauart |
| 7 | Z | Kesselwagen |
| 8 | I | Kühlwagen |
| 9 | U | Sonderwagen |

Stellen 6–8 kodieren Kennbuchstaben (Detailtabellen UIC 438).

## Reisezugwagen: 5.–8. Stelle (Prinzip)

- **5. Stelle:** Gattungsbuchstabe verschlüsselt (0 Post/Privat, 1 A Sitz 1. Klasse, 2 B, 3 AB, 4 Ac/ABc Liege 1. / gemischt, 5 Bc Liege 2., 6–8 Schlaf/Sonder, 9 Gepäck).
- **6. Stelle:** Abteilanzahl bzw. fiktive Abteile (Grossraum); bei Postwagen 0 = Postwagen.
- **7. Stelle:** Höchstgeschwindigkeit (0–2 bis 120 km/h, 3–6 bis 140, 7–8 bis 160, 9 über 160).
- **8. Stelle:** Heiz- und Energieversorgung (international relevant).

Zwischen 6. und 7. Stelle wird visuell oft ein **Bindestrich** gesetzt (Lesbarkeit).

## Selbstkontrollziffer (Luhn-Variante wie im Artikel beschrieben)

1. Nur die **ersten 11** Ziffern.
2. Von links: Ziffern abwechselnd mit **2** und **1** multiplizieren (erste Ziffer × 2).
3. Jedes Produkt in **Quersumme** zerlegen (z. B. 16 → 1+6), alle Quersummen addieren.
4. **Kontrollziffer** = Differenz der Summe zum **nächsten Vielfachen von 10**.

Beispiel aus dem Artikel: `31 81 665 0 286` mit Gewichtung 2,1,2,1,… ergibt Summe 40 → nächstes Zehnfaches 40 → Kontrollziffer **0** (Anschrift oft `…286-0`).

## Ordnungsnummer

Stellen 9–11: fortlaufend je Bauart; bei Güterwagen war die 8. Stelle historisch oft in die Ordnungsnummer „mitreingezogen“ (Anschrift ohne Lücken).

## Review-Hinweis

Modellartikel mit **Lok** oder **Triebfahrzeug:** diese Tabelle nur nutzen, wenn es wirklich um **Wagennummer** im JSON/Text geht.
