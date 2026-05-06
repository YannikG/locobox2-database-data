# Tschechien (ČD, ČD Cargo, Geschichte ČSD): Plausibilität für Locobox-Artikel

**Baureihen-Gesamtlisten (de.wikipedia):** **ČSD** (1945–1992, Tschechoslowakei) [«Liste der Lokomotiv- und Triebwagenbaureihen der ČSD»](https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CSD); **ČD** (ab 1993, Tschechische Bahnen) [«Liste der Lokomotiv- und Triebwagenbaureihen der ČD»](https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CD). Stichworte und Felder unten; Details in den Originaltabellen (siehe Provenienz).

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **CZ** für heutiges Tschechien; tschechoslowakisches **ČSD**-Vorbild oft **`CS`** (historisch), nach 1993 je Vorbild **CZ** oder **SK**; Exporte (DE, AT, SI, …) nur mit Text/Operator; **nicht** aus Baureihe raten |
| `operator` | **ČD**, **ČD Cargo** (Shop oft «CD» ohne Hächen); historisch **ČSD** (*Československé státní dráhy*, bis 1992; oft «CSD») |
| `electricSystem` | **3 kV DC** dominant; **25 kV 50 Hz**; **Mehrsystem** (z. B. 371, 383); **1,5 kV DC** für Altgrenzverkehr je nach Klasse |

## Baureihen-Stichworte (Loks, unvollständig)

- **Elektro:** **122** (Pendolino-Inland), **140**, **151**, **162 «Persing»**, **363** Mehrsystem, **371**, **380**, **383** Vectron-ähnlich.
- **Diesel:** **714** «Nokia», **721**, **742** «Zamračenka», **749**, **753** «Goggomobil», **771** «Grumpy» (Spitznamen nur zur Erkennung im Text).
- **Triebwagen:** **471** «RegioSpider», **650** «InterPanter», **844** «RegioShark» (Kategorien oft `triebzug`).

## Nachbarländer (vorsichtig)

- Viele **Škoda**- und **ČSD**-Baumuster liefen auch in **Slowenien** (JŽ/SŽ), **Slowakei** ([wiki-slowakei-zssk-loks-liste.md](wiki-slowakei-zssk-loks-liste.md)), teils **Österreich** und **Ungarn**. Plausibilität: ja; `country` automatisch ändern: **nein**, ohne Textbeleg.

## Split `type` / `number`

- Häufig «**363 129-4**»-Muster: dreistellige BR + Nummer mit Prüfziffer → Standard-Split.

## Review-Hinweis

- Stromsystem (3 kV vs. 25 kV vs. MS) vs. Baureihe; Lok vs. Triebzug-Kategorie → **Finding**.

## Provenienz

**Primär:**

- Tschechoslowakei **ČSD:** https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CSD  
- Tschechische Bahnen **ČD:** https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CD  

**Optional:** englischsprachige Übersicht «List of Czech locomotive classes» (Stromsystem / Diesel), falls eine Baureihe nur dort klar eingeordnet ist.

Inhalt dieser Datei **komprimiert offline**.
