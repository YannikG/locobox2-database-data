# Tschechien (ČD, ČD Cargo, Geschichte ČSD): Plausibilität für Locobox-Artikel

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **CZ** für inländisches Vorbild; Exporte (DE, AT, SI, …) nur wenn Text/Operator das zeigen |
| `operator` | **ČD**, **ČD Cargo**; historisch **ČSD** |
| `electricSystem` | **3 kV DC** dominant; **25 kV 50 Hz**; **Mehrsystem** (z. B. 371, 383); **1,5 kV DC** für Altgrenzverkehr je nach Klasse |

## Baureihen-Stichworte (Loks, unvollständig)

- **Elektro:** **122** (Pendolino-Inland), **140**, **151**, **162 «Persing»**, **363** Mehrsystem, **371**, **380**, **383** Vectron-ähnlich.
- **Diesel:** **714** «Nokia», **721**, **742** «Zamračenka», **749**, **753** «Goggomobil», **771** «Grumpy» (Spitznamen nur zur Erkennung im Text).
- **Triebwagen:** **471** «RegioSpider», **650** «InterPanter», **844** «RegioShark» (Kategorien oft `triebzug`).

## Nachbarländer (vorsichtig)

- Viele **Škoda**- und **ČSD**-Baumuster liefen auch in **Slowenien** (JŽ/SŽ), **Slowakei**, teils **Österreich** und **Ungarn**. Plausibilität: ja; `country` automatisch ändern: **nein**, ohne Textbeleg.

## Split `type` / `number`

- Häufig «**363 129-4**»-Muster: dreistellige BR + Nummer mit Prüfziffer → Standard-Split.

## Review-Hinweis

- Stromsystem (3 kV vs. 25 kV vs. MS) vs. Baureihe; Lok vs. Triebzug-Kategorie → **Finding**.

## Provenienz

Kompakt aus der englischsprachigen Wikipedia-Liste «List of Czech locomotive classes» (Gliederung nach Stromsystem und Diesel-Bauart).
