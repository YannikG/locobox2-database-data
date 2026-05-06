# Auszug: Baureihen der Deutschen Reichsbahn (DDR, 1945–1993)

## Zweck

Validierung und Nummern-Review für Triebfahrzeuge der **Deutschen Reichsbahn** in der **DDR** (1945 bis Fusion zur DB AG 1994). Ergänzt [wiki-db-baureihen-liste.md](wiki-db-baureihen-liste.md), die **nach** 1994 aus DB-Sicht fortgeschrieben ist. **Vorgänger** dieselben Kürzels **DR** in **1920–1945**: [wiki-dr-reichsbahn-1920-1945-baureihen-liste.md](wiki-dr-reichsbahn-1920-1945-baureihen-liste.md) (`country` dort **nicht** `DD`).

## Locobox-Felder (Kurz)

| Feld | Typische Erwartung |
|------|---------------------|
| `operator` | **`DR`** für Betrieb/Reichsbahn-Flotte in der DDR (nicht jedes Vorkommen von «DR» im Lacktext der **DB AG**). |
| `country` | Projektüblich **`DD`** (ISO-3166-1 alpha-2 historisch) für Reichsbahn-Kontext, wenn der Artikel die DDR-Flotte meint; nicht mit **DE** (Bundesrepublik / DB AG) verwechseln. |
| `model.type` / `number` | DR nutzte lange **Gattungs-/V-Bezeichnungen** (z. B. V 180, E 11), ab **1970** teils **numerisches Schema**, ab **1992** Angleich an das **DB-Baureihenschema** (drei Spaltenlogik in der Quelle). |

## Drei Nummerierungsebenen (Logik der Wikipedia-Tabelle)

In der Gesamtliste stehen oft **parallele** Bezeichnungen:

1. **Bis 1970:** DR-Gattung (z. B. **V 180**, **E 11**, **V 60**).
2. **Ab 1970:** DR-internes Zahlenformat (z. B. **118** aus V 180, **106** aus V 60).
3. **Ab 1992:** Bezeichnung nach **DB-Schema** (z. B. **228** für Teile der 118-Familie, **219**/**229** für Nachfolger der 119).

**Review-Hinweis:** Modellkarten und Shop-/Herstellertexte mischen Epochen; dieselbe physische Lok kann in Daten als «118», «V 180» oder später «228» erscheinen. Bei Split **Epoche und Beschreibung** mitziehen, nicht nur die erste Zifferngruppe.

## Stichproben: Diesel (Kohärenz mit DB-Liste)

| DR-Ära (Gattung / DR-Zahl) | Später DB-Schema (Auszug) | Anmerkung |
|----------------------------|---------------------------|-----------|
| V 180 → 118.x | 228.x | gleiche Familie, unterschiedliche Umbau- und Achs-Teilfamilien |
| 119 | 219, 229 | 229 = Hochgeschwindigkeits-Umbau-Teilserie |
| 130 → 132 | 232, **234**, 242 | **234** auch nach DB AG weiter umgebaut; mit DB-Baureihe **234** (Diesel) verwechslungsfrei halten, nicht mit E-Lok **103** |

## Stichproben: Elektro

- **E 11** → **211**; Nachfolger **243** / DB **143**-Linie (Detailkette in Originaltabelle).
- **E 44** → **244**; **E 42** → **242** mit DB-**142**.
- **E 251** / **251** / **171:** Sonderfall **25 kV 50 Hz** (Rübeland); nicht pauschal wie 15 kV-Reihen behandeln.
- Viele DR-E-Loks: **15 kV / 16,7 Hz** (Tabelle verweist darauf; Mehrsystem-Ausnahmen einzeln prüfen).

## Triebwagen / Akku

Separate Kapitel **Dieseltriebwagen**, **Elektrotriebzüge**, **Akkufahrzeuge** in der Quelle; für **Triebzüge** oft keine einzelne Lok-Ordnungsnummer im Shop-Titel → Split wie im Projekt üblich oder Finding «Set ohne Einzelnummer».

## Review-Hinweis

- **DR** in `operator` plus Epoche **IV** (DDR) ist ein starker Hinweis auf **`country: "DD"`**, aber **Lackbeschriftung «DR»** bei späterem Museums- oder DB AG-Modell ist **kein** alleiniger Beweis für Reichsbahn-Betrieb.
- Bei Unsicherheit **unklar** markieren; Originaltabelle als **Struktur** nutzen, nicht als Ersatz für Primärquelle am Modell.

## Provenienz

Struktur (Dampf, Diesel, Triebwagen, Elektro, Elektrotriebzug, Akku) und Baureihen-Mappings aus der deutschsprachigen Wikipedia «Liste der Lokomotiv- und Triebwagenbaureihen der Deutschen Reichsbahn (1945–1993)»: https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_Deutschen_Reichsbahn_(1945%E2%80%931993)
