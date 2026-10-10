# Auszug: Liste der Lokomotiven und Triebwagen der ÖBB

## Zweck des Artikels

Übersicht über **Baureihen (RH)** der Österreichischen Bundesbahnen: in Betrieb, zukünftig, ausgemustert, Bahndienst; tabellarisch mit Spitznamen, Einsatz, Antrieb, vmax, Stromsystem.

## Aussprache / Schreibweise

**Vierstellige Reihen** werden in Österreich oft **paarweise** gesprochen (Beispiel aus dem Artikel: „1044“ = „Zehn-Vierundvierzig“).

## In Betrieb (Beispiel-Reihen, kein Anspruch auf Vollständigkeit)

**Elektroloks (Auszug):** 1016, 1063, 1064, 1116 (Taurus-Familie), 1144, 1163, 1216, 1293 (Vectron), …

**Elektrotriebwagen (Auszug):** 4010/4110 KISS, 4020/4023/4024/4124 Talent, 4744/4746/4748 Desiro ML, …

**Dieselloks (Auszug):** 2016 Hercules, 2067/2068, 2070 Hector, 2080/2180 Schneeschleuder, 2143, …

**Dieseltriebwagen (Auszug):** 5022 Desiro, 5047, …

## Zukünftig / Ausgemustert

Separate Tabellen für geplante Reihen (z. B. Coradia Stream, KISS-Varianten, Mireo, …) und ausgemusterte Baureihen mit Verkauf, Umbau, Museumsbestand.

## Review-Hinweis

- `model.type` wie **1116 195-9** → Baureihe **1116** plausibel zu ÖBB; Betriebsnummer und Prüfziffer separat prüfen (Luhn nur wenn alle Ziffern sicher extrahiert).
- Keine Baureihe erzwingen: wenn Nummer unbekannt, **unklar**.

## Locobox-Validierung (Kurz)

| Feld | Erwartung |
|------|-----------|
| `country` | **AT** (Ausnahmen nur mit Text, z. B. Railjet in DE/CH) |
| `operator` | **ÖBB**, **ÖBB Nightjet**, **Rail Cargo Austria**; Nightjet-Wagen ≠ Lok |
| `electricSystem` | **15 kV 16,7 Hz** üblich; Mehrsystem (**1216**, **1293**, …) laut Vorbild |

## Provenienz

Kompakt aus der deutschsprachigen Wikipedia-Liste «Liste der Lokomotiven und Triebwagen der ÖBB».
