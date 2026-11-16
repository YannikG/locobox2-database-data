# RhB / MGB / Schmalspur-Naming (Review)

Komprimiert für Locobox-Split und Plausibilität bei **Meterspur-/Bosnischer-Spur**-Vorbildern (häufig BEMO). Ergänzt [wiki-schweizer-bauartbezeichnungen.md](wiki-schweizer-bauartbezeichnungen.md). Kein Betriebsnachweis.

## Locobox-Regel (hart)

| Feld | Inhalt |
|------|--------|
| `model.type` | Nur **Bauart / Serie** (z. B. `Ge 4/4 II`, `HGe 4/4 II`, `Uah`, `Lb-v`) |
| `model.number` | **Betriebsnummer** bzw. Ordnungsnummer (z. B. `614`, `105`, `2881`) |
| `model.livery` | Taufname, Werbe-/Sonderlack, Zugname aus Anführungszeichen |
| `categories` | Antrieb/Gattung (`elektrolokomotive`, `zahnradlokomotive`, `gueterwagen`, …) |

**Nicht** in `type`: Shop-Wörter wie Universallok, Werbelok, Nostalgielok, Diesellok, Zahnradlok, Dampflok-Fertigmodell (siehe [wiki-bemo-shop-parsing.md](wiki-bemo-shop-parsing.md)).

Operator-Kürzel (`RhB`, `MGB`, …) gehören in `model.operator`, nicht vor die Bauart in `type` (Parser strippt sie).

## Schweizer Bauart: Ge / HGe (Kurz)

Aus dem CH-System 1902–1989 (Schmalspur behält es weitgehend):

| Teil | Bedeutung |
|------|-----------|
| **G** | Schmalspur, Adhäsion |
| **H** | Zahnrad (oft kombiniert **HG** / **HGe**) |
| **e** | elektrisch; **m** thermisch |
| **4/4** | 4 Triebachsen / 4 Achsen gesamt |
| römisch **I / II / III** | Generation **derselben Bahn** mit gleicher Grundbauart |

Beispiel: **Ge 4/4 II** = meterspurige elektrische Adhäsionslok, Bo’Bo’, zweite Generation bei dieser Bahn.

## Rhätische Bahn (RhB)

`operator` **RhB**, `country` **CH**, Spur Vorbild **1000 mm** → Modell oft `H0m` / `0m`.

### Elektroloks (Stammnetz / Bernina)

| Bauart | Typische Nummern | Locobox |
|--------|------------------|---------|
| Ge 4/4 **I** | 601–610 | `type` `Ge 4/4 I`, `number` dreistellig |
| Ge 4/4 **II** | **611–633** | `type` `Ge 4/4 II`, `number` z. B. `614` |
| Ge 4/4 **III** | 641–652 (bzw. 641–653 je Liste) | `type` `Ge 4/4 III` |
| Ge 4/4 (Bernina, ohne römisch) | historisch 81/82, später **181** / **182** | `type` `Ge 4/4`, `number` `181` oder `182` |

**Ge 4/4 II Namensgebung:** Loks tragen **Ortsnamen** Graubündens (z. B. 614 «Schiers», 616 «Filisur»). Das ist **`livery`** (oder Namensschild), nicht Teil von `type`. Werbefolierungen (Alpine Classic Pullman, «100 Jahre Chur - Disentis», Login, …) ebenfalls `livery`.

**Split-Beispiel:** Shop `RhB Ge 4/4 II 614 Universallok "Schiers"` → `type` **`Ge 4/4 II`**, `number` **`614`**, `livery` **`Schiers`**.

### Personenwagen / Speisewagen (Auszug Import)

Gattungsbuchstaben wie bei CH/UIC-Personenwagen; RhB-Nummern oft vierstellig.

| Gattung (Beispiel) | Bedeutung (grob) | Kategorie |
|--------------------|-------------------|-----------|
| **A** | 1. Klasse | `personenwagen` |
| **Ap** / **Api** | Panorama / Glacier-Express-Familie | `personenwagen` |
| **Bp** | 2. Klasse Panorama | `personenwagen` |
| **WR** / **WR-S** / **WRp** | Speisewagen / Salon / Panorama-Speise | `personenwagen` |

`type` = Gattungszeichen (inkl. Bindestrich-Varianten wie `WR-S`), `number` = Wagennummer.

### Güterwagen (UIC-Gattung + Kennbuchstaben)

RhB schreibt modern oft **UIC-Gattung** + Kleinbuchstaben, z. B.:

| Zeichen | Locobox `type` | Kategorie |
|---------|----------------|-----------|
| **Lb-v** | `Lb-v` | `gueterwagen` |
| **Sb-v** | `Sb-v` | `gueterwagen` |
| **Za** | `Za` | `gueterwagen` (Kessel) |

Werbefolien auf Container-/Schiebewandwagen (Traveco, Volg, …) → `livery`, nicht `type`.

## Matterhorn Gotthard Bahn (MGB)

`operator` **MGB**, `country` **CH**. Nachfolge von **FO** und **BVZ**; viele Fahrzeuge ex FO/BVZ umgezeichnet.

### HGe 4/4 II

Kombinierte **Zahnrad- und Adhäsions**-Ellok (Bauart **HGe 4/4**, Generation **II**).

| Herkunft | Nummernkreis (Vorbild) | Locobox |
|----------|------------------------|---------|
| ex FO | **101–108** | `type` `HGe 4/4 II`, `number` z. B. `105` |
| ex BVZ | **1–5** | `type` `HGe 4/4 II`, `number` einstellige Betriebsnummer |

Taufnamen (Oberalp, Glacier Express-Bezug, Berge, …) → `livery`. Kategorie **`zahnradlokomotive`** (+ `lokomotive`), nicht bloss «Elektrolok» ohne Zahnrad-Hinweis.

### Güterwagen MGB

Beispiel Import: **Uah** + Nummer (Knickkessel) → `type` `Uah`, `number` `2881`, `gueterwagen`.

## Österreichische Schmalspur (BEMO-Scope)

Bosnische Spur **760 mm** → Modell oft **`H0e`**. `country` **AT**.

### Steiermärkische Landesbahnen (StLB / Steiermarkbahn)

| Typ | Locobox | Hinweis |
|-----|---------|---------|
| **VL 22**, **VL 23** | `type` **`VL 22`** / **`VL 23`**, `number` **`null`** | Klassenbezeichnung **ist** der Typ; «23» ist **keine** separate Betriebsnummer |
| | | Herkunft JŽ **740**; modernisiert bei StLB |

**Nicht** splitten in `type` `VL` + `number` `23`.

### Zillertalbahn (ZB / ZVB)

| Typ | Locobox | Hinweis |
|-----|---------|---------|
| **D 10** | `type` **`D 10`**, `number` **`null`** | Hausbezeichnung der Diesellok (ex JŽ-Umfeld); analog VL |

## DR-Baureihe 99 (Schmalspur-Dampf)

`operator` **DR**, Schmalspur-Dampfloks unter Sammelbaureihe **99**.

| Schreibweise Vorbild | Locobox |
|----------------------|---------|
| `99 732` / `DR 99 732` | `type` **`DR 99`**, `number` **`732`** |
| EDV/HSB-Formen `99 1594-3` | `type` **`DR 99`**, `number` **`1594-3`** |

`country`: oft **DE**; bei klarer DDR-/HSB-Epoche IV+ ggf. Finding **DD** (nicht raten ohne Epoche/Text). Scale Modell oft **`H0e`**.

## K.Sä.Sts.B. (Sachsen, Historik)

Königlich Sächsische Staatseisenbahnen. Shop-Titel `K.Sä.Sts.B. No. 6` → `operator` **`K.Sä.Sts.B.`**, `type` **`No.`**, `number` **`6`**, `country` **DE**.

## Plausibilität Schnellcheck

1. RhB Ge 4/4 **II** mit Nummer ausserhalb **611–633** → Finding (ausser Werks-/Museumssonderfall im Text).
2. RhB **181/182** mit römischem **II/III** → falsch; Typ ohne römisch.
3. MGB HGe ohne Zahnrad-Kategorie → Finding.
4. StLB/ZB `VL …` / `D …` mit erzwungener `number` → zurücknehmen.
5. Wagen-Gattung in `type`, Werbefolien in `livery`.

## Provenienz

- [Bauartbezeichnungen der Schweizer Lokomotiven und Triebwagen](https://de.wikipedia.org/wiki/Bauartbezeichnungen_der_Schweizer_Lokomotiven_und_Triebwagen)
- [Ge 4/4](https://de.wikipedia.org/wiki/Ge_4/4)
- [RhB Ge 4/4 II](https://de.wikipedia.org/wiki/RhB_Ge_4/4_II)
- [Rhätische Bahn § Rollmaterial](https://de.wikipedia.org/wiki/Rh%C3%A4tische_Bahn#Rollmaterial_der_RhB)
- [HGe 4/4 II](https://en.wikipedia.org/wiki/HGe_4/4_II) / [Matterhorn-Gotthard-Bahn](https://de.wikipedia.org/wiki/Matterhorn-Gotthard-Bahn)
- [StLB VL 11–16](https://de.wikipedia.org/wiki/StLB_VL_11%E2%80%9316) (Kontext VL 22–23 / JŽ 740)
- [Zillertalbahn](https://de.wikipedia.org/wiki/Zillertalbahn) (D 10)
- [Baureihe 99](https://de.wikipedia.org/wiki/Baureihe_99)
- UIC Güterwagen-Gattungen: [UIC-Bauart-Bezeichnungssystem für Güterwagen](https://de.wikipedia.org/wiki/UIC-Bauart-Bezeichnungssystem_f%C3%BCr_G%C3%BCterwagen)
