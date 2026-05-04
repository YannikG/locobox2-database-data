# Auszug: Liste der Lokomotiv- und Triebwagenbaureihen der Deutschen Bahn

## Zweck

Übersicht über Baureihen von **DB Regio**, **DB Fernverkehr**, **DB Cargo** und **Deutsche Bahn AG**, die nach **1. Januar 1994** noch im Einsatz waren oder sind. Keine vollständige DR/DB-Geschichte.

## Nummerierung / Rechtliches (Kurz)

- Baureihen folgen dem **Baureihenschema der Deutschen Bundesbahn**, 1994 von der DB AG übernommen.
- **Eisenbahn-Bundesamt** ab 2007: nationales Fahrzeugeinstellungsregister; Vergabe über **UIC-Baureihenschema Triebfahrzeuge**; öffentliche Liste „Baureihen im Fahrzeugeinstellungsregister“ existiert parallel.
- Interne DB-Baureihennummern können von Registerangaben abweichen.

## Legende (Spaltenlogik)

- **Dampf:** Spalte „Nr.“ = verbliebene Betriebsnummern.
- **Sonst:** Spalte **BR** = Baureihe; in Klammern _(…)_ = bei DB AG (ausser Museum) nicht mehr im Betrieb.
- **\*** an Baureihe: oft kurz angemietet, Beschriftung kann beim Voreigentümer bleiben.
- **Name:** Spitznamen kursiv; frühere Nummern z. B. „ex DB 103“.
- **Antr.:** DKo/DÖl (Dampf), elR/elD (Elektro Reihenschluss/Drehstrom), de/dh/dm (Diesel), Akk, H², usw.
- **vmax:** km/h; Dampf teils getrennt vorwärts/rückwärts.
- **Stromsystem:** Mehrfacheintrag = Mehrsystemlok; **16,7 Hz** vs **16 ⅔ Hz** im Betrieb praktisch vernachlässigbar.

## Struktur der Liste (Kapitel)

Dampfloks; Elektroloks; Dieselloks; Hybrid/Zweikraft; Kleinloks; elektrische Triebwagen; Akku- und Wasserstofftriebwagen; Dieseltriebwagen; Bahndienst; Ausland.

## Dieselloks: relevante Baureihen für Nummern-Review (Auszug)

| BR | Kurzinhalt |
|----|------------|
| 201–204, 211–214, 218, 218.8, 218.9 | V 100-Familie, 218 Universal, Varianten |
| 215–217, 225, 226 | V 160-Familie, Umbauten |
| 219, 228, 229 | DR 119 / V 180-Linie |
| 232, 232.9, 233, (234), 241 | Ludmilla-Linie DR 130/132; **234** = modernisierte 232, Wendezug, vmax 140, weitgehend abgestellt/verkauft |
| 245, 246, 247, 266.4 | Traxx/Vectron DE usw. |
| 290–298, 291–296 | V 90-Rangierfamilie und Umbauten |

**234 xxx-x** gehört zur **Diesel-Baureihe 234** (Ludmilla-Nachfolger), **nicht** zur E-Lok **103**.

## Elektroloks: Stichproben für Kohärenzchecks

101, 102, **103** (ex E 03, Fernverkehr/Nostalgie), 105, 110–115, 120, 143, 152, … (Vollliste im Originalartikel).

## Review-Hinweis

- Erste Ziffer(n) der Betriebsnummer = oft Baureihe (**103 222-6** → Baureihe 103).
- Klammern in der Wikipedia-Liste **(_103_)** = ausser Betrieb bei DB AG; Modell kann trotzdem historisch korrekt sein.
- Bei Unsicherheit **unklar** statt Wikipedia-Zitat.

## Locobox-Validierung (Kurz)

| Feld | Erwartung |
|------|-----------|
| `country` | **DE** (Ausland nur mit Text/Operator) |
| `operator` | **DB**, **DB Cargo**, **DB Fernverkehr**, **DB Regio**, historisch **DR**-Bezug in Epoche IV |
| `categories` | Dampf/Elektro/Diesel/Triebzug/Hybrid gemäss Baureihe und Epoche |

## Provenienz

Kompakt aus der deutschsprachigen Wikipedia-Liste «Liste der Lokomotiv- und Triebwagenbaureihen der Deutschen Bahn» (Struktur und BR-Tabelle).
