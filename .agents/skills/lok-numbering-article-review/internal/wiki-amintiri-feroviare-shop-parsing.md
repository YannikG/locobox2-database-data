# Amintiri Feroviare / AF Models: Shop-Artefakte (Review)

Komprimiertes Wissen für Imports von **amintiriferoviare.com** (Hersteller) und Händler-PDPs (häufig **menzels-lokschuppen.de**). **Import-Workflow:** Skill [locobox-import](../../locobox-import/SKILL.md), CLI-Source `amintiri-feroviare` / Alias `af`. Vorbild-Plausibilität: [wiki-rumaenien-loks-liste.md](wiki-rumaenien-loks-liste.md), [wiki-bulgarien-loks-liste.md](wiki-bulgarien-loks-liste.md), [wiki-ungarn-loks-liste.md](wiki-ungarn-loks-liste.md).

## Kontext

Artikelnummern oft **ohne** Präfix im offiziellen Shop (`10024`), Händler mit **`AF`**-Präfix (`AF10201`). Locobox speichert die Nummer **ohne** `AF` (Ausnahme SKUs wie `L131526`).

## Typische Artefakte

| Artefakt | Bedeutung | Review / Parser |
|----------|-----------|-----------------|
| Titel `… \| Menzels Lokschuppen` | Händler-Suffix | aus `model.type` streichen |
| `vorbestellen`, `Ep.6`, `Epoche 6` im Typ | Shop-Rest | streichen; Epoche → `model.era` |
| Rumänisch `Vagon …`, `Locomotiva …`, `drmit` | Rohsprache / Tippfehler | auf kurze Bauart/Gattung normalisieren (AVA200, T2s, Zagkks, …) |
| `HGD31001` im Typ | Händler-/Partner-SKU im Titel | Typ = Wagenbauart; SKU bleibt `articleNumber` |
| Anführungszeichen / Taufnamen | *Puma*, *Hora*, *Delfinul*, *King Carol I*, *Mátyás Hunyadi*, EXPRESS, PNRR | → `livery` |
| OCR `Dalphin` | gemeint **Delfinul** / The Dolphin | Livery kanonisch **Delfinul** |
| `CFR Infrast.` | CFR Infrastructura | Operator **CFR Infra** |
| Suchseiten-HTML als PDP | Fetch-Fehler | nicht parsen; `source.url` darf keine reine Suche sein |

## SKU und Varianten

| Muster | Bedeutung |
|--------|-----------|
| `10xxx` | Elektro / klassische 060-EA / EA-3000 / TRAXX (Analog) |
| `12xxx` / `L13….` | Dampf |
| `19xxx` | oft **DCC/Sound**-Schwester zu `10xxx` (gleiche Familie) |
| `20xxx` / `22xxx` / `25xxx` | Personenwagen / Sets |
| `30xxx` / `31xxx` / `35xxx` / `502xxx` | Güter / Kühl / Sets |

Schwester Analog/Sound: gleiche letzten Ziffern, Präfix 10↔19 (z. B. `10201` / `19201`). Stromsystem am **Modell** setzen; Text oft für beide Varianten gleich → nicht blind von der Schwester kopieren.

Wagen: `electricSystem` **`Unbekannt`**.

## Operator / Land (kurz)

- Default-Netz RO; BDZ / Bulmarket / DB Cargo Bulgaria → **BG**; MÁV → **HU**.
- Details: Länder-Wikis oben.

## Search / PDP

- Offiziell: `cauta?caut={nummer}` → Link `/produs/…`.
- Fallback Händler: Menzels-Suche `AF{nummer}`; nur echte Produktdetail-URL behalten.
- Marker `<!-- locobox-pdp-url: … -->` → `source.url`.

## Sets

- ICE Mihai Eminescu **mit Lok** → Lok-Datei behält Set-SKU; Kategorien `lokomotive` + Antrieb.
- **Reisezugwagen-Sets** (z. B. `25001`, `25008`–`25011`): **nicht** `Reisezugwagen-Set` / `Liegewagen-Set` als `type`. Pro Wagen eine JSON-Datei mit konkreter Gattung (`AVA200`, `AcBcmee`, `Bpmz`/`Bpmbz`, …), `setNumber` = Shop-SKU, Zusatzwagen als `{sku}-2` / `{sku}-bpmbz` (wie Roco `{sku}-blm`).
- Nachzügler **nur Wagen** → alle Teile `personenwagen`, nicht Elektro-Lok.

## Provenienz

Shop-Beobachtung amintiriferoviare.com und Menzels AF-Listings; Länderwissen in den verlinkten `wiki-*-loks-liste.md`.
