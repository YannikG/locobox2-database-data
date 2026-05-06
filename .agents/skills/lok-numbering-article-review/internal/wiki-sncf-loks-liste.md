# Frankreich (SNCF): Plausibilität für Locobox-Artikel

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **FR**, ausser grenzüberschreitendem Vorbild oder Import (dann Text/Operator) |
| `operator` | **SNCF**, **SNCF Réseau**, **Fret SNCF**, **Captrain** (früher), **Thello** (eingestellt), Regionalmarken; **Keolis** / **Transilien**-Umfeld nur wenn Text passt |
| `categories` | `elektrolokomotive` / `diesellokomotive` / `dampflokomotive` / `triebzug` muss zum **Antrieb** im Fliesstext passen |
| `electricSystem` | Häufig **1,5 kV DC** (Altnetz), **25 kV 50 Hz AC** (LGV und modernes Netz), **Mehrsystem** bei Grenz- und Güterloks (z. B. «Sybic»-Familie) |

## Baureihen- und Schreibweisen (Stichworte, nicht vollständig)

- **Elektro-Loks (Gattung):** Präfixe **BB** (Zweimotorig-Zweiachser-Tradition), **CC** (dreiteilig Co-Co), modern **Prima**, **Traxx**, **Vectron**-Derivate; Hochgeschwindigkeit **TGV** (Triebzug, nicht als klassische «Baureihe + Ordnungsnummer» behandeln).
- **Diesel:** **A1AA1A 62000**, **BB 75000**-Linie, **Y**-Verschiebeloks; **Gasturbine** historisch (selten Modellfälle).
- **Dampf:** Historische Achsfolge-Buchstaben und SNCF-**Reihennummern**; Museums- und Dampfbahn-Vorbilder oft Sondernummer.
- **Triebzüge:** **TGV**, **Régiolis**, **Coradia** usw. → meist `triebzug`, nicht mit Einzellok-Baureihe verwechseln.

## Split `type` / `number`

- Französische Shop-Strings oft «**BB 26000**» oder «**222 009-9**»-artig: Baureihe vs. EVN-Teil an Leerzeichen splitten, wenn das Vorbild einheitlich so geführt wird; bei **TGV** oft Zug-/Rame-Bezeichnung, nicht Lok-BR.
- Punktnotation **seltener** als bei AT/CH; eher **Leerzeichen** oder reine BR-Zahl plus Nummer.

## Grenzfälle

- **Mehrsystem:** Stromsystem im JSON muss zum Vorbild passen (nicht «dc» setzen, wenn 25 kV AC im Text).
- **Livery / Marketing:** Sonderfolierung (Werbezüge) nicht in `type`/`number` halten (siehe `field-parsing-model.md`, Livery nach Split).

## Review-Hinweis

- Widerspruch **Kategorie** vs. Fliesstext-Antrieb, oder BR vs. Epoche (z. B. TGV-Baustelle vs. Dampf) → **Finding**.

## Provenienz

Kompakt aus der deutschsprachigen Wikipedia-Liste «Liste der Lokomotiven und Triebwagen der SNCF» (Ausgangspunkt für Gliederung; keine Pflicht zum Nachlesen beim Review).
