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
| `X4630, rouge crème, …` | `X 4630` | null | Rest |
| `Z 27877, …` | `AGC` | `27877` | Rest |
| `DB Cargo Vectron MS, … "I am …"` | `Vectron MS` | null | Kurzname / Quote |
| `Apm EC Panorama, …` | `Apm EC Panorama` | null | Rest |

SNCF BB/CC: Serie vs. Laufnummer wie [reference-sncf-type-number.md](../reference-sncf-type-number.md); BB 222xx → Serie `BB 22200`.

## Kategorien

- HLE / BB / CC / Vectron / Smartron → `lokomotive` + `elektrolokomotive`
- `X####` / Autorail / EAD → `triebwagen` + `dieseltriebwagen` (**ohne** `lokomotive`)
- AGC / `Z #####` → `triebwagen` + `elektrotriebwagen`
- Apm / Bpm / I2 / I10 / M6 / OCEM / WL → `wagen`

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
