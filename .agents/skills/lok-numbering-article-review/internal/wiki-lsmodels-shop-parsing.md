# LS Models Shop (lsmodels.eu) – Parsing / Review

PrestaShop auf **lsmodels.eu**. Katalog-SKUs oft mit Leerzeichen (`16 075` → `16075`). Sound-`S` und Models-World `MW…` sind in Catalog-Extract vorerst übersprungen.

## Typische PDP-Felder

| Feature | Locobox |
|---------|---------|
| `ALIMENTATION` DC/AC | `electricSystem` (DC-Analog / AC-Digital, …) |
| `ECHELLE` HO | `scale` → `H0` |
| `EPOQUE` | `era` |
| `PAYS` | oft **EVU-Name** (`SNCF`, `SNCB`), nicht ISO – Parser mappt auf Operator+Land |
| `TYPE DE MATERIEL` | HLE/HLD/AM/AUT → Kategorien |
| `CATEGORIE` | Serie-Hinweis (`HLE 13`, `BB 22000`, `VECTRON`, `AGC`) |
| H1 / `og:title` | Rohquelle für `type` / `number` / `livery` |

Shop oft ohne UVP (`show_prices: false`).

## Title-Split (Allowlist)

| H1-Muster | `type` | `number` | `livery` |
|-----------|--------|----------|----------|
| `1312, Grau-blau, … LINEAS` | `HLE 13` | `1312` | Rest |
| `1347 blanche / wit (SNCB/NMBS)` | `HLE 13` | `1347` | Rest |
| `HLE 13 SNCB/NMBS` | `HLE 13` | null | null |
| `BB 22200, grau/violett, …` | `BB 22200` | null (Serie) | Rest |
| `BB 22399, …` / `BB 22240, …` | `BB 22200` | `22399` / `22240` | Rest |
| `CC 6507, …` | `CC 6500` | `6507` | Rest |
| `X4630, rouge crème, …` / `X4638-XR8650, bleu, …` | `X 4500` (Nr. 4501–4800) | `X 4630` / `X 4638` | Rest |
| `Z 27877, …` | `AGC` | `27877` | Rest |
| `DB Cargo Vectron MS, … "I am …"` | `Vectron MS` | null | Kurzname / Quote |
| `Apm EC Panorama, …` | `Apm EC Panorama` | null | Rest |

SNCF BB/CC: Serie vs. Laufnummer wie [reference-sncf-type-number.md](../reference-sncf-type-number.md); BB 222xx → Serie `BB 22200`.

## Kategorien

- HLE / BB / CC / Vectron / Smartron → `lokomotive` + `elektrolokomotive`
- `X####` / Autorail / EAD → `triebwagen` + `dieseltriebwagen` (**ohne** `lokomotive`)
- AGC / `Z #####` → `triebwagen` + `elektrotriebwagen`
- Apm / Bpm / I2 / I10 / M6 / OCEM / WL → `wagen`

## Betriebsnummer aus dem Produktbild

Viele LS-Models-Titel nennen nur die Serie (`BB 22200`, `BB 7200`, `CC 6500`, `HLE 27`, `BR 120`, `Vectron`), die Laufnummer steht aber auf dem Bild `source.imageUrl` (`…superlarge_default/…jpg`, 4800×1600). Bild laden und ansehen, Details und Regeln: `SKILL.md` → «Betriebsnummer aus Produktbild lesen».

- SNCF-Flanke `522214` → `BB 22214` (`number` `22214`); `107284` → `BB 7284`; `CC-6513` → `6513`
- HLE: grosse Nummer an der Flanke (`2756`, `2114`, `1211`), UIC-Zeile ignorieren
- DB BR 120/Vectron: `120 144-1` bzw. UIC `91 80 6193 366-2 D-DB` → `193 366-2`
- Autorail `X####`: Nummer steht im Titel/Beschreibung (`X4638-XR8650`), nicht im Bild suchen → `type` `X 4500`, `number` `X 4638`
- Stadtwappen/Taufnamen (z. B. «Dole») kurz in `livery`, Muster `En Voyage, Dole`

## AC/DC-Schwestern

LS Models: oft DC `AAxxx` und AC `AA5xx` (+500 auf der Artikelnummer, z. B. `16075` / `16575`). Primär `ALIMENTATION` aus dem PDP. Fehlt `ALIMENTATION` (häufig ausverkaufte Seiten ohne Feature-Block) und die DC-Schwester (`articleNumber − 500`) liegt im Repo mit gleichem `model.type` und nicht-AC-Stromsystem, darf Auto-Fix die +500-Variante auf `AC-Digital` setzen. Nicht aus dem Fliesstext der Schwester raten und nicht kopieren, wenn Typen abweichen. `model.era`: wenn eine Twin-Seite `EPOQUE` hat und die andere `Unbekannt`, bei gleichem `type` die bekannte Epoche übernehmen (gleiche Vorbild-Epoche). Epoche nicht aus Lack oder Marketing erfinden.

## Auto-Fix

- Parser: `tools/cli/.../lsmodels/parse_pdp.py` (`split_lsmodels_title`)
- Review-Skript: `scripts/autofix_lsmodels_shop_import.py` (Dry-Run, dann `--apply`)

## Pass-1-Checks

- Langer H1 noch in `model.type`?
- `PAYS=SNCF` aber `country=DE` / `operator=Unbekannt`?
- AGC/X als `lokomotive` ohne Triebwagen-Kategorie?
- Wagen (Apm/Bpm) als Lok kategorisiert?
- HLE-Nummer nur in `type` (`1312, …`) ohne Split?

## Provenienz

Shop-PDPs lsmodels.eu; Neuheiten-Folder unter news.lsmodels.eu/mailing/pdf/.
