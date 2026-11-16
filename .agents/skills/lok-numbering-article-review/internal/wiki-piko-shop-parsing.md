# PIKO Webshop: Titel-Artefakte und Lesarten (Review)

Komprimiertes Wissen für **Loknummerierung und Plausibilität** nach Import aus `piko-shop.de`. **Import-Workflow:** Skill [locobox-import](../../locobox-import/SKILL.md).

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
| Shop-Slug **Diesel-/Elektrotriebwagen** | Kategorie | `triebwagen` + `dieseltriebwagen` / `elektrotriebwagen` (**ohne** `lokomotive`); siehe Autofill-Skript |
| Anführungszeichen um **`"Stadler"`** bei GTW 2/6 | **Fahrzeughersteller / Typenname**, nicht Lackierung | Livery aus Rest des Titels (THURBO, HLB, StB, …), nicht «Stadler» |
| **`bwegt`** bei THURBO-Titeln | Shop-Tippfehler für **«bewegt»** (Werbefolierung) | ignorieren; Livery **THURBO**, nicht «bwegt» |
| **`operator`: «Privatbahn»** | Shop-Platzhalter statt EVU | Land/EVU aus Livery und Fliesstext ([wiki-privatbahn-livery-anker.md](wiki-privatbahn-livery-anker.md)); Tippfehler **«Privatbahhn»** wie Privatbahn behandeln |
| **`operator`: «Privatbahn»** + klarer EVU-Anker | Shop-Platzhalter | Operator auf EVU setzen; `country` nach [wiki-privatbahn-livery-anker.md](wiki-privatbahn-livery-anker.md) (z. B. Medway/E.494→**IT**, EP Cargo→**CZ**, Green Cargo DK→**DK**) |
| **`187 002 TX Logistik Railpool`** (UIC ohne **`BR`**) | Shop-Titel ohne Baureihenpräfix | Split: `type` **`BR 187`**, `number` **`002`**, `livery` **`TX Logistik Railpool`**; Regel **`piko_uic_br`** in `autofix_piko_shop_type.py` |
| **`D.141 1019`** / **`D.145 2004`** / **`D.141.1023`** | FS-Baureihe + Betriebsnummer | Split: `type` `D.141` / `D.145`, `number` Ziffernblock; Regeln **`piko_fs_d_num`** / **`piko_fs_d_dot`** |
| **`Vectron E.191 EVM Rail`** / **`Vectron EB 3200`** | Marketing «Vectron» + Klasse | `type` **`E.191`** + Livery **`EVM Rail`**, bzw. `type` **`EB 3200`** |
| **`EN 57 PKP IV`**, **`ET 21 PKPC`**, **`EU43 PR`**, **`Serie 52 SNCB`** | Operator/Epoche noch im Typ | auf Baureihe kürzen (`EN 57`, `ET 21`, `EU43`, `Serie 52`) |
| **`Start-Set mit Bettung … Taurus/SM42/G7/…`** | Startset-Marketingtitel | `type` auf bekannte Lokbezeichnung (z. B. **`1216`**, **`SM42`**); Set-Inhalt nicht als Livery |
| Livery **`… + 3 Güterwagen`**, **`mit 2 …wagen`**, **`VI, 3-tlg`**, **`ICE 4 … Klimaschützer`** | Setlänge/Epoche/Sondername vermischt | Livery bereinigen oder löschen; Sonderlack **`Klimaschützer`** beibehalten |

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
