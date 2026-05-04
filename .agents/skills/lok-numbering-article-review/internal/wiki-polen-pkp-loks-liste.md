# Polen (PKP): Plausibilität für Locobox-Artikel

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **PL** |
| `operator` | **PKP Intercity** (Fernpersonen), **PKP Cargo** (Güter), **PKP SKM**, **Koleje Mazowieckie**, **Polregio** usw. je nach Modelltext |
| `electricSystem` | **3 kV DC** weit verbreitet; **25 kV AC** auf ausgebauten Strecken und bei Mehrsystemloks; Import **15 kV**-Umlauf nur mit Text |
| `categories` | Viele **elektrolokomotive** und **triebzug** (ED, EN, Elf, Dart, …); Dampf eher Museum |

## Baureihen-Präfixe (Stichwort, nicht vollständig)

- **EU** … TRAXX/ Vectron MS / EU44-ähnlich.
- **EP** … Personen-E-Loks (z. B. EP09).
- **ET** … Triebzüge elektrisch.
- **ED** … elektrische Triebzüge (Doppelstock-Linien).
- **SM** … Diesellok Rangier/Strecken.
- **ST** … Dieseltriebwagen.
- **SU** … Co-Co-Diesel klassisch.

## Schmalspur und Ausland in PL

- **Schmalspur:** Waldbahnen, Oberlausitz-Bezug im Text → `scale`, `minRadiusMm`.
- **«Im Ausland besessen, in Polen eingesetzt»:** Operator und `country` nicht nur aus BR raten.

## Split `type` / `number`

- Typisch «**EU07-015**» oder «**ET22-697**»; Präfix+BR in `type`, Rest in `number`, wenn der Shop nicht schon getrennt liefert.

## Review-Hinweis

- 3 kV vs. Mehrsystem vs. Kategorie; PKP-Operator vs. Regionalgesellschaft widersprüchlich → **Finding**.

## Provenienz

Kompakt aus der englischsprachigen Wikipedia-Liste «List of PKP locomotives and multiple units» (Dampf / Diesel / Elektro / DMU / EMU).
