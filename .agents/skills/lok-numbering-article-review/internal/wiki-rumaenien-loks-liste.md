# Rumänien (CFR): Plausibilität für Locobox-Artikel

Kontext **Căile Ferate Române** (CFR): deutschsprachiger Wikipedia-Artikel [«Căile Ferate Române»](https://de.wikipedia.org/wiki/C%C4%83ile_Ferate_Rom%C3%A2ne) (Netz, Gesellschaften; siehe Provenienz). Eine **einzige** dewiki-Gesamtliste aller Triebfahrzeugbaureihen wie bei anderen Ländern fehlt oft; Baureihen über Einzelartikel und Fachliteratur abstützen.

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **RO** |
| `operator` | **CFR** (*Căile Ferate Române*), **CFR Călători** (Personen), **CFR Marfă** (Güter); private **Grup Feroviar Român** usw. nur wenn Text passt |
| `electricSystem` | Sehr häufig **25 kV 50 Hz AC**; ältere **3 kV DC**-Loks noch im Bestand / Museum |
| `categories` | **EMU/DMU** klar von Lok trennen (Transrapid ausserhalb, nicht CFR-Standard) |

## Baureihen-Stichworte (unvollständig)

- **Elektro:** **40** (Co-Co-Klassiker), **41** (Bo-Bo), **47** (Modernisierung/Remotorisierung), **480** TRAXX, **LE** Softronic-Neu- und Umbauten (Epoche beachten).
- **Diesel:** **60** «Ludmilla»-Derivat, **65** «Sulzer»-Linie, **69** GM-Typen, **80** Shunter-ähnlich (grobe Einordnung).
- **Triebzüge:** **Hyperion**, **Desiro**, **Pesa**-Umfeld je nach Jahrzehnt.

## Split `type` / `number`

- CFR-Shopstrings oft «**47 7xx-x**» oder «**40 0xx-x**»; BR und Nummernteil splitten wie bei DB/ÖBB, wenn der String eindeutig zweiteilig ist.

## Grenzfälle

- **Museum vs. Betrieb:** alte **060-EA**-Ära vs. moderne AC; Epoche im JSON (`era`) mit Bild abgleichen.
- **Umbau:** gleiche Nummer, andere Unterbau (Remotor) → Text «ex …» lesen.

## Review-Hinweis

- Lok-Kategorie mit Triebzug-Beschreibung oder 3 kV vs. 25 kV Widerspruch → **Finding**.

## Provenienz

**Primär (CFR, deutsch):** https://de.wikipedia.org/wiki/C%C4%83ile_Ferate_Rom%C3%A2ne

**Ergänzend (Dampf-Museumslok-Übersicht, deutsch):** https://de.wikipedia.org/wiki/Liste_in_Rum%C3%A4nien_vorhandener_Dampflokomotiven

**Ergänzend (englisch, Rollmaterial-Übersicht):** https://en.wikipedia.org/wiki/Rolling_stock_of_the_Romanian_Railways

Inhalt dieser Datei **komprimiert offline**.
