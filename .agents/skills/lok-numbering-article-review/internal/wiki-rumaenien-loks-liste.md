# Rumänien (CFR / Privatbahnen): Plausibilität für Locobox-Artikel

Kontext **Căile Ferate Române** (CFR): deutschsprachiger Wikipedia-Artikel [«Căile Ferate Române»](https://de.wikipedia.org/wiki/C%C4%83ile_Ferate_Rom%C3%A2ne) (Netz, Gesellschaften; siehe Provenienz). Keine einzige dewiki-Gesamtliste aller Baureihen; Stütze über Einzelartikel, Shoptexte und Fachliteratur. Häufiger Importkontext: **Amintiri Feroviare / AF Models** → [wiki-amintiri-feroviare-shop-parsing.md](wiki-amintiri-feroviare-shop-parsing.md).

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **RO** für CFR und rumänische Privatbahnen. Nicht **BG**/ **HU**, nur weil Softronic/TransMontana auch dort fährt |
| `operator` | Staatsnah: **CFR**, **CFR Calatori** (Personen; Locobox ohne Diakritika ok), **CFR Marfa** (Güter), **CFR Infra** (Infrastruktur, Shop oft «CFR Infrast.»). Privat nur bei Textbeleg |
| `electricSystem` | Vorbild oft **25 kV 50 Hz AC**; ältere **3 kV DC** möglich. Am **Modell** trotzdem `DC-Analog` / `DC-Digital` (H0-Zweileiter), nicht Blind-AC setzen |
| `categories` | Lok vs. Wagen klar; ICE-/Zugsets mit Lok → `lokomotive`+Antrieb; reine Wagennachzügler → `personenwagen` |

## Operator-Anker (häufig in AF-/Shoptexten)

| Text / Shop | Locobox `operator` | `country` |
|-------------|--------------------|-----------|
| CFR, Căile Ferate Române | **CFR** | RO |
| CFR Calatori / Călători | **CFR Calatori** | RO |
| CFR Marfa / Marfă | **CFR Marfa** | RO |
| CFR Infra / Infrastructura / Infrast. | **CFR Infra** | RO |
| Astra Trans Carpatic / ATC | **Astra Trans Carpatic** | RO |
| Vest Trans Rail / VTR | **VTR** | RO |
| Constantin Group / Grup | **Constantin Group** | RO |
| Green Cargo (RO-Umlauf Softronic) | **Green Cargo** | RO (wenn Text Rumänien) |
| DB Schenker Rail Romania / DB Cargo Romania | **DB Schenker Rail Romania** bzw. **DB Cargo** laut Text | RO |
| GFR / Grup Feroviar Român | **GFR** | RO |
| Rompetrol / Rompetrol Logistic | **Rompetrol** / **Rompetrol Logistic** | RO |
| Petrom, Lukoil, Azomures, Petraom, Bulrom | Eigenname wie im Text | RO |
| ARF (Test-/Probe-TRAXX) | **ARF** | RO |

## Baureihen-Stichworte

- **Elektro (klassisch):** Bauart **060-EA** = CFR-Klasse **40** (Co-Co); Varianten **060-EA1**, Lacknamen **Hora**, **Puma**, «rote Kabinen». Klasse **41** (Bo-Bo). Klasse **47** = modernisierte 060-EA (IGBT; Taufname oft **Delfinul** / Shop-OCR «Dalphin»).
- **Elektro (neu):** Softronic **TransMontana** (UIC oft `91 53 0 480…` / `481…`, Taufnamen *King Carol I*, *Queen Maria*); Bombardier/Alstom **TRAXX** / **TRAXX3** (z. B. MAV `480-005`, ARF-Testlack).
- **Diesel:** Bauart **060-DA**; Klassen **60**, **62** (Shop «60-0362-8», «62-0548-8» → `type` Klasse, `number` Laufteil). Weitere: **65**, **69**, Rangier **80**-Umfeld.
- **Dampf:** Serie **150.xxxx** (Shop `150.0054` / `150.1076`) → Split `type` **`150`**, `number` vierstellig ohne Punkt.
- **Wagen (AF-häufig):** **AVA200** (auch Salon/Bar/Schlaf), **T2s**, **Bcm** (ex-DB Liegewagen), **Y/B-70**, Kessel **Zagkks** / **Zackks**, Kühl **Rsfwc** / **Icehqs**, offene **Eaos**, UIC-Namen **Bremen** / **Linz** / **Villach** / **Klagenfurt**.

## Split `type` / `number`

- «**47 7xx-x**», «**40 0xx-x**», «**41-0189-1**»: Klasse/Bauart in `type`, Rest in `number`.
- «**060-DA-222**»: `type` **`060-DA`**, `number` **`222`**.
- «**60-0362-8**» / «**62-0548-8**»: `type` **`60`** bzw. **`62`**, `number` **`0362-8`** / **`0548-8`**.
- TransMontana/TRAXX: Produktname oder Baureihe in `type`; volle EVN oder `480 xxx` in `number`, wenn im Text eindeutig.
- Taufnamen / EXPRESS / PNRR / Delfinul → **`livery`**, nicht in `type` lassen.

## Grenzfälle

- **060-EA vs. Klasse 40/47:** gleiche Familie; Text «class 47» / «Delfinul» → eher `type` **`47`** plus Livery.
- **ATC vs. CFR:** Titel «ATC» oder «Astra Trans Carpatic» → Operator **nicht** CFR.
- **Grenzverkehr BG/HU:** BDZ-/MÁV-Artikel → [wiki-bulgarien-loks-liste.md](wiki-bulgarien-loks-liste.md) / [wiki-ungarn-loks-liste.md](wiki-ungarn-loks-liste.md); `country` nach Betreiber, nicht nach Herstellerland RO.
- **Epoche fehlt** im Shoptext → `era` **`Unbekannt`**, nicht raten.

## Review-Hinweis

- Lok-Kategorie mit reinem Wagenset (z. B. ICE-Nachzügler ohne Lok) → Finding / Kategorie korrigieren.
- «blau» nur wegen «CFR Calatori» im Satz → **kein** Livery-Raten.

## Provenienz

**Primär (CFR, deutsch):** https://de.wikipedia.org/wiki/C%C4%83ile_Ferate_Rom%C3%A2ne

**Ergänzend (Dampf):** https://de.wikipedia.org/wiki/Liste_in_Rum%C3%A4nien_vorhandener_Dampflokomotiven

**Ergänzend (englisch, Rollmaterial):** https://en.wikipedia.org/wiki/Rolling_stock_of_the_Romanian_Railways

**Shop-Import AF Models:** [wiki-amintiri-feroviare-shop-parsing.md](wiki-amintiri-feroviare-shop-parsing.md)

Inhalt dieser Datei **komprimiert offline**.
