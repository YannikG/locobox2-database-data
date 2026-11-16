# SNCF: `model.type` und `model.number` (Locobox-Konvention)

Gilt für Shop-/Katalog-Importe (Roco, PIKO, …) mit französischen Präfixen **BB**, **CC**, **Y**, … und einem Ziffernblock. Nicht mit DB-«BR + Prüfziffer» verwechseln.

## Kernregel

| Was der Shop zeigt | Bedeutung | Locobox |
|--------------------|-----------|---------|
| Nur **Serienbezeichnung** (z. B. «BB 26000», «CC 72000») | Klasse / Serie, **keine** konkrete Lok | `type` = volle Serie (`BB 26000`), `number` = **`null`** |
| **Konkrete Betriebsnummer** (z. B. «CC 6514», «BB 26022») | Serie + Laufnummer | `type` = **Serie** (`CC 6500`, `BB 26000`), `number` = **volle Anschrift-Ziffern** (`6514`, `26022`) |

**Verboten (häufiger Auto-Fix-/Parserfehler):**

- `type` = `BB` und `number` = `26000` (Serie in `number` geparkt)
- `type` = `CC` und `number` = `72000`
- Serie mit Endung **`000`** als «Laufnummer» behandeln

## Serie vs. Laufnummer erkennen

1. **Beschreibung / `og:title` / URL-Slug** zuerst lesen.
2. Endet der Ziffernblock auf **`000`** und es gibt **keine** abweichende Einzelnummer im Text → **nur Serie**, `number` null.
3. Weicht die Nummer von der Serienbasis ab (z. B. **6514** bei Serie **CC 6500**, **26022** bei **BB 26000**) → Serie in `type`, volle Ziffern in `number`.
4. Serienbasis bei fünf Stellen: `(Ziffernblock // 1000) * 1000` (z. B. `72052` → Serie `72000`). Bei vier Stellen oft `(n // 100) * 100` (z. B. `6514` → `6500`), nur wenn Serie im Text/Wiki zum Operator passt.

## Beispiele (Roco Neuheiten 2019)

| Artikel | Shop | `type` | `number` |
|---------|------|--------|----------|
| 73857 / 73858 | Elektrolokomotive **BB 26000** | `BB 26000` | `null` |
| 73004 / 73005 | Diesellokomotive **CC 72000** (2. Serie) | `CC 72000` | `null` |
| 73398 / 73399 / 79399 | Elektrolokomotive **CC 6514** (Serie CC 6500, TEE) | `CC 6500` | `6514` |

BB 26000 («Sybic»): Betriebsnummern typisch **26001–26234**. Steht im Shop nur «BB 26000», fehlt die Laufnummer → nicht erfinden.

## Andere SNCF-Formen

| Muster | Hinweis |
|--------|---------|
| `Serie 232 TC` (Dampf) | Alles sinnvoll in `type`, `number` null, sofern keine Einzelnummer |
| `Y` + Ziffern (Rangier) | Wie Serie/Laufnummer; bei Unklarheit Finding |
| TGV / Régiolis / Coradia | **Triebzug**, nicht BB/CC-Split; Kategorien `triebzug` / ggf. `triebwagen`; Ramennummer (z. B. TGV n°17) darf in `number` |
| UIC-Sechser (`467471`, `567556`, `167424`) auf BB/CC | `type` = Serie (`BB 67400`, …), `number` = **volle** Anschriftziffern |
| BB 67400 inkl. 676xx | Serie heisst **BB 67400** (nicht `BB 67600`) |

## Kategorien

- Klassische BB/CC-**Lok** → `lokomotive` + `elektrolokomotive` bzw. `diesellokomotive`
- **Elektrotriebwagen** (auch wenn Shop-Pfad unter `elektrolokomotiven/` liegt) → `triebwagen` + `elektrotriebwagen` (**ohne** `lokomotive`)

## REE Modèles Shop (häufige Reste)

REE-Parser legen oft **dieselbe** Anschrift in `type` **und** `number` (`BB 9282` / `BB 9282`) oder lassen lange Shop-Titel stehen.

| Shop / Roh | `type` | `number` |
|------------|--------|----------|
| BB 9282 / BB 9263 (Serie BB 9200) | `BB 9200` | `9282` / `9263` |
| BB 16001 (Serie BB 16000) | `BB 16000` | `16001` |
| BB 25188 (Serie BB 25100) | `BB 25100` | `25188` |
| BB 25200 nur Serie | `BB 25200` | `null` |
| BB 9300 / BB 9317 | `BB 9300` | `null` / `9317` |
| CC 7136 (Access / CC 7100) | `CC 7100` | `7136` |
| BB 63792 / BB 63010 (BB 63000/63500) | `BB 63000` | `63792` / `63010` |
| RGP 1 + X-2730 | `RGP 1` | `X-2730` |

**Dampf (Pacific / Mikado, REE «MACHINE …»):**

| Shop | `type` | `number` |
|------|--------|----------|
| `MACHINE 2-231K 8 NORD` | `231 K` | `2-8` |
| `4-231 G 222 Tours` | `231 G` | `4-222` |
| `141 D 318` | `141 D` | `318` |

Regionpräfix (`1-`…`5-`) gehört zur laufenden Nummer (`{region}-{engine}`), nicht in `type`.

## Auto-Fix

Skript `autofix_model_type_number_split.py` (nur wenn `number` noch **null**):

- Regel **`sncf_bb_cc_5`**: Fünferblock **nicht** auf `000` → `type` = `{BB|CC} {Serie000}`, `number` = voller Block (z. B. `CC 72052` → `CC 72000` / `72052`).
- Regel **`sncf_bb_cc_4`**: Viererblock **nicht** auf `00` → `type` = `{BB|CC} {Serie00}`, `number` = voller Block (z. B. `CC 6514` → `CC 6500` / `6514`).
- Reiner Serienstring `BB 26000` / `CC 72000` / `CC 6500` → **kein** Split.

Nach altem Fehl-Split (`type` BB, `number` 26000): zurück zu `type` `BB 26000`, `number` null.

Skript **`autofix_ree_shop_import.py`** (REE-Shop, auch wenn `number` schon gesetzt):

- **`ree_sncf_bbcc_*`**: Präfix aus `number` entfernen, Serie in `type` (inkl. BB 9200 / 16000 / 25100 / 63000 / CC 7100).
- **`ree_steam_*`**: MACHINE / «Locomotive à vapeur» → `231 K|G` / `141 D` + Nummer; Kategorie `dampflokomotive`.
- Kurztypen Moyse / 040 DE / CFL 852 / RGP 1; Operator/Epoche aus Text wenn noch `Unbekannt`.

## Verweise

- Überblick FR: [internal/wiki-sncf-loks-liste.md](internal/wiki-sncf-loks-liste.md)
- Allgemeine Split-Tabelle: [internal/field-parsing-model.md](internal/field-parsing-model.md)
- REE-Autofix: [scripts/autofix_ree_shop_import.py](scripts/autofix_ree_shop_import.py)

## Provenienz

Locobox-Konvention aus Import Roco Neuheiten 2019 (BB 26000 / CC 72000 / CC 6514), SNCF-Serienpraxis (BB 26000 = Sybic, Nummernkreis 26001–26234) und REE Modèles Shop-Importe (BB 9200 / 16000 / 25100, CC 7100 Access, Pacific 231 K/G).
