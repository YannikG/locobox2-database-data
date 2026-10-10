# Auszug: Eindeutige Fahrzeugnummer (europäische Fahrzeugnummer, EVN; umgangssprachlich oft TSI-Nummer)

## Zweck

Zwölfstellige Nummer zur eindeutigen Kennzeichnung von Eisenbahnfahrzeugen in Europa und angrenzend angewandten Staaten. Vergabe über staatliche Regelwerke (TSI/ETV im EU-Raum; historisch UIC-Vorgaben).

## Aufbau (12 Stellen, logische Felder)

| Stelle(n) | Bedeutung (Kurz) |
|-----------|------------------|
| 1 | Fahrzeugtyp und Interoperabilitätseignung |
| 2 | Typbezogen |
| 3–4 | Land der Registrierung (UIC-Ländercode) |
| 5–8 | Technische Merkmale des Fahrzeugs |
| 9–11 | Ordnungsnummer |
| 12 | Selbstkontrollziffer |

**Spezial:** Bei Triebfahrzeugen, deren Nummer mit **9** beginnt (ausser definierte Sonderfahrzeuge), können Stellen 3–8 **national** geregelt sein.

## Erste Ziffer: grobe Fahrzeugklasse

| Erste Ziffer | Bedeutung |
|--------------|-----------|
| 1–4, 8 | Güterwagen (Gattungslogik UIC-Wagen) |
| 5–7 | Reisezugwagen ohne Eigenantrieb |
| 9 | Triebfahrzeuge (inkl. Triebzüge, bestimmte Beiwagen) sowie Sonderfahrzeuge; Sonderfahrzeuge oft mit **9** an definierter Position |

## Geschichte (nur Kontext)

UIC führte ab 1960er Jahren EDV-taugliche Wagennummern mit Prüfziffer; Triebfahrzeuge lange freiwillig oder verkürzt. Ab EU-Entscheidung 2006/920 wurden UIC-Codes zunehmend **Ländercodes**; Nummern bleiben oft beim Verkauf ins Ausland. Übergang zu ETV-Kennzeichnung u. a. ab 2015 schrittweise relevant.

## Review-Hinweis

Volle 12 Stellen im Modelltext = zuerst erste Ziffer prüfen (Wagen vs Triebfahrzeug). Keine Güterwagen-Gattungstabelle auf Lok anwenden.
