# Ungarn (MÁV): Plausibilität für Locobox-Artikel

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **HU** |
| `operator` | **MÁV** (*Magyar Államvasutak*), Güter **MÁV Cargo**; historische und Museumsbezeichnungen im Text |
| `electricSystem` | Viel **25 kV 50 Hz AC** (Hauptnetz); ältere / Spezialfälle im Modelltext prüfen |
| `categories` | Dampf-Anteil historisch gross; moderne Artikel meist Elektro oder Diesel |

## Historische Nummerierung (Dampf-Review)

- **1911:** grosses Umnummerierungsjahr; alte Dampf-Fotos können **zwei** Nummerierungslogiken zeigen → `description` und Epoche abgleichen, nicht nur eine Zahl aus dem Shop übernehmen.

## Baureihen-Stichworte (unvollständig)

- **Elektro:** **V43** (klassisch), **431**, **470** «Kármán»-Umfeld, **480** TRAXX, moderne Mehrsysteme.
- **Diesel:** **M41**, **M62** «Szergej», **M47**; Rangier **M44**, **M32**-Umfeld (grobe Orientierung).
- **Dampf:** Viele Serien mit **375**, **424**, **01**-ähnlichen historischen Bezügen im ungarischen Netz (nur Plausibilität, nicht für Einzelnummer ohne Text).

## Split `type` / `number`

- Ungarische EVN-ähnliche Schreibweise oft «**431 001**»; BR in `type`, Rest in `number`, wenn klar getrennt.

## Grenzfälle

- **Schmalspur:** Balatonfüredi, Lillafüred usw. → `scale`, `minRadiusMm`, Text «760 mm» etc.
- **Grenzverkehr:** mit AT/SK/RO kombinierte Umläufe im Text prüfen.

## Review-Hinweis

- Dampf-Kategorie mit Elektro-BR oder umgekehrt → **Finding**.

## Provenienz

Kompakt aus der englischsprachigen Wikipedia-Liste «List of Hungarian locomotives» (Struktur Dampf / Diesel / Elektro / Schmalspur).
