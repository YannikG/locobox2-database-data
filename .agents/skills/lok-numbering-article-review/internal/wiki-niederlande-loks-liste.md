# Niederlande (NS, ProRail-Umfeld): Plausibilität für Locobox-Artikel

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **NL** |
| `operator` | **NS** (Personenverkehr), **NS International** (Grenze), Güter **DB Cargo NL**, **Lineas**, **RFO** usw. je nach Epoche; historisch **NS**-Vorgänger |
| `scale` | Normalspur meist **h0**; Schmalspur-Modelle explizit im Text (museum, Veluwe, …) |
| `categories` | Triebwagen häufig (Koploper, ICM, SLT, FLIRT, …); Loks weniger, aber **1600/1700/1800/1900**-Serien und TRAXX-Importe üblich |

## Stromsystem

- **1,5 kV DC:** klassisches NL-Netz.
- **25 kV AC:** HSL-Zubringer und internationale TRAXX-/Multisystem-Loks (Betrieb NL-Anteil im Text prüfen).

## Baureihen-Stichworte (Lok und Triebzug, unvollständig)

- **Elektroloks:** **1600** (Altbau), **1700**, **1800**, **189** (TRAXX MS), **193** (Vectron-ähnliche Einsätze im NL-Kontext möglich).
- **Diesel:** **2200**, **6400**, historisch **2400**-Umfeld.
- **Triebzüge:** **ICM/Koploper**, **VIRM**, **SLT**, **DDZ**, **FLIRT 3**; Güter-NL eher Lok.

## Split `type` / `number`

- Niederländische Schreibweise oft «**193 759**» oder «**1736**» nur BR: wie üblich BR in `type`, Nummer in `number`, wenn EVN-Teil vorhanden.

## Grenzfälle

- **Grenzverkehr:** `country` kann NL bleiben, wenn Vorbild klar NL-Einsatz; sonst BE/DE mitabgleichen.
- **Import-Roco:** Artikelnummer und Shop-URL oft korrekt, Fliesstext manchmal deutsch mit BR aus Nachbarland → Operator prüfen.

## Review-Hinweis

- Widerspruch Kategorie (Triebzug vs. Lok) oder 1,5 kV vs. 25 kV im Text → **Finding**.

## Provenienz

Kompakt aus der deutschsprachigen Wikipedia-Liste «Liste von Lokomotiv- und Triebwagenbaureihen der Niederländischen Eisenbahn».
