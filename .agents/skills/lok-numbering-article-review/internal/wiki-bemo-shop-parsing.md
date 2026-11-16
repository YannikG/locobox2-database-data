# BEMO Shop / Katalog: Titel-Artefakte (Review)

Komprimiertes Wissen für Imports von **bemo-modellbahn.de** und BEMO-Neuheiten-PDFs. **Import-Workflow:** Skill [locobox-import](../../locobox-import/SKILL.md). Naming Vorbild: [wiki-rhb-mgb-schmalspur-naming.md](wiki-rhb-mgb-schmalspur-naming.md).

## Kontext

Shop-Titel mischen **Bauart**, **Betriebsnummer**, **Marketingrolle** und **Taufname**. Locobox `model.type` darf nur die Bauart behalten.

## Typische Artefakte (nicht in `model.type`)

| Artefakt im Roh-Titel | Bedeutung | Review / Parser |
|-----------------------|-----------|-----------------|
| **Universallok**, **Werbelok**, **Nostalgielok**, **Rangierlok** | Shop-Rollenwort | streichen; Lack/Name → `livery` |
| **Zahnradlok**, **Diesellok**, **Dampflok**, **Dampflok-Fertigmodell** | Produktgattung / Verpackung | streichen; Kategorie setzen (`zahnradlokomotive`, `diesellokomotive`, `dampflokomotive`) |
| **Exclusivmodell 2026** | Marketing | streichen |
| Operator-Präfix **RhB**, **MGB**, **StLB**, **ZB**, **DR**, **K.Sä.Sts.B.** | EVU | `model.operator`, nicht im `type` |
| Anführungszeichen **«Schiers»**, **"Alpine Classic…"** | Taufname / Folie | `model.livery` |
| Leeres / nur Artikelnummer als H1 | Theme-Bug | Fallback `<title>` ohne «– BEMO Modelleisenbahnen» |

## SKU und Varianten

| Präfix (7-stellig) | Typische Bedeutung |
|--------------------|--------------------|
| **12** / **13** | H0m Analog / Digital |
| **10** / **11** | H0e Analog / Digital |
| **92** / **93** / **99** | 0m Analog / Digital (99 oft Sound/Digital-Variante) |
| **22** / **32** / **95** | Wagen H0m / 0m |

Schwester: gleiche letzten 5 Ziffern, Präfix 12↔13, 10↔11, 92↔93/99. Stromsystem am **Modell** (`DC-Analog` / `DC-Digital`), nicht Vorbild-Fahrleitung.

Wagen: `electricSystem` **`Unbekannt`** (kein Triebfahrzeug).

## Search / PDP

- Kompakte Suche `?s=1258164` ist leiser als spaced; PDP-URL muss `/produkt/…` sein.
- HTML-Marker `<!-- locobox-pdp-url: … -->` bzw. finale Fetch-URL → `source.url` (nie die Such-URL behalten).
- Treffer ohne passende `.single_artnr` verwerfen (Zubehör-Fallen).

## Provenienz

Shop-Beobachtung bemo-modellbahn.de; Vorbild-Naming [wiki-rhb-mgb-schmalspur-naming.md](wiki-rhb-mgb-schmalspur-naming.md).
