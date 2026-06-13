# PIKO Webshop: Titel-Artefakte und Lesarten (Review)

Komprimiertes Wissen für **Loknummerierung und Plausibilität** nach Import aus `piko-shop.de`. **Kein** Import-Runbook (Parser, Kampagnen-Tags, Katalog-PDFs liegen ausserhalb dieses Skills).

## Kontext

PIKO-Shop-Titel und die in `description` eingebetteten Attributzeilen sind **Marketing plus Technikdaten**. Vor Split und Plausibilitätscheck Rohstrings bereinigen (mental oder via Repo-Skript, siehe `SKILL.md` → «Repo-Skripte»).

## Typische Titel-Artefakte (nicht in `model.type` behalten)

| Artefakt im Roh-Import | Bedeutung | Review-Aktion |
|------------------------|-----------|---------------|
| Präfix **`Sound-`** / **`Sound-`** mitten im Typ | Sound-Variante (Marketing) | aus `model.type` entfernen; Stromsystem separat (siehe `field-parsing-model.md` → Modell-Stromsystem) |
| Suffix **`, inkl. PIKO Sound-Decoder`** / **`SoundDecoder`** (ohne Bindestrich) | Werk-Sound | aus `model.type` entfernen |
| Präfix **`N `**, **`H0 `**, **`TT `** am Titelanfang | **Spur** des Modells | nicht als Baureihe interpretieren; `model.scale` ist massgebend |
| **`Wechselstromversion`** / **`Wechselstrom`** im Titel | AC-Modellvariante | aus `model.type`; `model.electricSystem` prüfen (Modell-Enum, nicht Vorbild-kV) |
| **`Elektotriebwagen`** (fehlendes «r») | PIKO-Schreibweise | gleichbedeutend mit Elektrotriebwagen; kein eigener Typ |
| Anführungszeichen um **`"Stadler"`** bei GTW 2/6 | **Fahrzeughersteller / Typenname**, nicht Lackierung | Livery aus Rest des Titels (THURBO, HLB, StB, …), nicht «Stadler» |
| **`bwegt`** bei THURBO-Titeln | Shop-Tippfehler für **«bewegt»** (Werbefolierung) | ignorieren; Livery **THURBO**, nicht «bwegt» |
| **`operator`: «Privatbahn»** | Shop-Platzhalter statt EVU | Land/EVU aus Livery und Fliesstext ([wiki-privatbahn-livery-anker.md](wiki-privatbahn-livery-anker.md)); Tippfehler **«Privatbahhn»** wie Privatbahn behandeln |

## Niederlande: `Rh` + Ziffernblock

PIKO N-Importe für NS-Loks liefern oft:

- `model.type`: **`Rh`**
- `model.number`: **`1100`**, **`1200`**, **`2200`**, …

Das ist **kein Split-Fehler**: **Rh** = Klassenpräfix (Niederlande), Ziffernblock = **Baureihen-/Klassennummer**, keine UIC-Betriebsnummer. **Nicht** in Pass 1 als «type zu kurz» oder «Rh only» bemängeln, wenn `number` gesetzt ist und Beschreibung/URL `Rh 1100` o. ä. bestätigen.

## Sets und Triebzüge (Kurzverweis)

Lange `model.type`-Strings ohne EVN: siehe [field-parsing-model.md](field-parsing-model.md) → «Sets und Triebzüge ohne Betriebsnummer».

## Schwester-Varianten (Kurzverweis)

Sound / Gleichstrom / Wechselstrom am gleichen Modell: [field-parsing-model.md](field-parsing-model.md) → «PIKO Variantengruppen».

## Bewusst ausserhalb dieses Skills

- **`releaseDate`** / Kampagnen-**`tags`**
- **`categories`** aus Shop-URL
- Katalog-PDF vs. Shop-Vollständigkeit
- Parser-Fehler in Nebenfeldern (z. B. `minRadiusMm` aus Sound-Decoder-Artikelnummer) → Finding «Parser-Artefakt», kein Nummern-Split

## Provenienz

Aus Locobox-Review **PIKO Neuheiten 2024** (`piko-neuheiten-2024`): wiederkehrende Shop-Titel, N-Skala ohne `Stromsystem:`-Zeile, GTW/Stadler/THURBO-Fälle, NL-Rh-Konvention.
