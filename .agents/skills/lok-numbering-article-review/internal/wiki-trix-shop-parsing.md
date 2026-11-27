# Trix Produktdatenbank: Import und Review

Ergänzt [wiki-maerklin-shop-parsing.md](wiki-maerklin-shop-parsing.md) (gleiche HTML-Form, gleicher Parser). Hier nur, was bei Trix anders ist.

## Kontext

- PDP: `https://www.trix.de/de/produkte/details/article/{nr}` (Host `www.trix.de` steht in der Allowlist).
- `parse_trix_pdp` ruft `parse_maerklin_pdp` auf und überschreibt nur Marke/ID/Notiz, `electricSystem` (Trix H0 = **DC**, Märklin = AC) und einige Betreiber-Zusatzregeln (`_EXTRA_OPERATORS`: Dispolok, PEG, NYC, Angel Trains Cargo, Film-Design → «Fiktiv», Gleisbau-Firma/Museumslok → «Privatbahn», preussische Gattung → KPEV).
- Fotos liegen auf `static.maerklin.de` (auch bei Trix). `source.imageUrl` = erster `<a href=…damcontent….jpg>`. Bei **älteren Artikeln (ca. vor 2010)** ist das Foto nur **800 px** breit (kein 1500-px-Original vorhanden); Nummern lassen sich dort nur teilweise lesen.

## Inventur (Stand 27.11.2026)

- Liste: `trix.de/de/produkte/trix-h0/lokomotiven?tx_torrpdb_list[filter]=3&…[perpage]=36&…[page]=N` (793 Artikel auf 23 Seiten, inkl. ausverkauft). Die Liste enthält bei lieferbaren Artikeln den **UVP** (`399,00 €`), ausverkaufte Artikel haben keinen Preis.
- «Packungen» (`/trix-h0/packungen`) und Minitrix sind eigene Listen und nicht im Scope.
- Ausgeschlossen werden Titel mit «Zugpackung», «Set mit …», «…-Doppelset», «…-Doppelpackung», «… mit Mannschaftswagen».
- Seiten, die der Shop nicht mehr kennt (ca. 50 KB, `<title>Details | Trix Websites`, kein `damcontent`), liefern kein Foto: `source.imageUrl` bleibt leer.

## Erstjahr / Tag

PDP-Abschnitt «Veröffentlichungen» (`<span class="block"> - Neuheiten 2003</span> …`): kleinste vorkommende Jahreszahl; «bis 2000» zählt als 2000. Tag `trix-neuheiten-JJJJ` (`kind: neuheiten`). Artikel ohne Katalogeintrag (Werbe-/Sonderprodukte) bleiben ohne Tag und ohne `releaseDate`.

## Typische Artefakte (zusätzlich zu Märklin)

| Artefakt | Regel |
|----------|-------|
| `Baureihe E 10.12` wird zu `BR E 10` | Parser brach an Dezimalpunkten ab; behoben (Punkt nur vor Leerraum/Ende). |
| `BR EP 3/6`, `BR SVT 04`, `BR Köf II`, `BR ET 91`, `BR EB 3200` | `BR` entfällt vor Länderbahn-/Sondergattungen (`EP 3/6`, `SVT 04`, `Köf II`, `ET 91`, `EB 3200`). |
| `Reihe RAm TEE I 501`, `Serie RAe TEE II`, `Reihe Dm3` | Reihe/Serie/Bauart/Gattung vor Buchstaben-Bezeichnungen entfällt; rein numerisch (`Reihe 2016`, `Serie 1200`) bleibt. |
| `Rh 638` bei ÖBB | `Rh` nur bei NL; sonst `Reihe`. |
| `Be 6/8III` | `Be 6/8 III`. |
| `Dampftriebwagen Bauart Kittel CidT` | `Kittel CidT`. |
| `BR 01 150` / `BR V 140 001` ohne Nummer | Split in `BR 01` + `150`. |
| Klammerzusatz `(ex Baureihe 52)`, `(ehemalige preussische G 12)`, `(Serie 420)` | aus `type` entfernen. |
| `Schienenbus VT 95.9 mit Einachs-Anhänger …` | `VT 95.9`. |
| Spitz-/Werbenamen («Roter Pfeil», «Koploper», «Wismarer Schienenbus», Sondereditionen) | nach `model.livery`. |
| H1 nur «Elektrolokomotive.» und **kein** Vorbild-Text (alte Artikel) | Typ bleibt Klassenwort, `Unbekannt` als Betreiber → Finding. |

Autofix-Kette: `autofix_trix_shop_import.py` → `autofix_model_type_number_split.py` → `autofix_model_country.py` → `autofix_maerklin_shop_import.py` → **`autofix_trix_review.py`** (diese Regeln, nur `model.type`/`model.number`). Einzelfälle (Betreiber, Livery, Kategorie) per `articles patch`.

## Betriebsnummer aus Foto

800-px-Fotos: etwa 40 % der Nummern lesbar. Übernommen werden nur `high` sowie `medium` mit Prüfziffer-Bestätigung oder ohne «unscharf»-Vermerk. Länderbahn-/Sondergattungen: keine Plausibilitätsregel über die Baureihe. Fiktive Beschriftungen und Typ = Nummer (z. B. `F 1200`) nicht als `number` übernehmen.
