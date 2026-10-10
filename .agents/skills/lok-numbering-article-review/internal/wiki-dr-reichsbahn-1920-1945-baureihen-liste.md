# Auszug: Baureihen der Deutschen Reichsbahn (1920–1945)

## Zweck

Validierung und Nummern-Review für Triebfahrzeuge der **Deutschen Reichsbahn** in der **Weimarer Republik und im NS-Staat** (1920 bis 1945): Einheitsloks, Gattungsbezeichnungen, Übergänge zur späteren **Bundesbahn**-Logik. **Nicht** identisch mit der **DDR-Reichsbahn** (1945–1993), siehe [wiki-dr-ddr-baureihen-liste.md](wiki-dr-ddr-baureihen-liste.md).

## Locobox-Felder (Kurz)

| Feld | Typische Erwartung |
|------|---------------------|
| `operator` | **`DR`** für die staatliche **Deutsche Reichsbahn** dieses Zeitraums (Text/Lack «DR» kann auch bei Museums- oder Nachkriegsmodellen vorkommen; Kontext prüfen). |
| `country` | **`DD` gilt nicht**: das Kodewort ist für die **DDR** (1949ff.) reserviert. Für 1920–1945 typischerweise **`DE`** (heutiges Deutschland als Nachfolgeterritorium) oder je nach Modell **historisch bewusst** dokumentieren; bei Grenz-/Besetzungsfällen **unklar** statt raten. |
| `model.type` / `number` | Häufig **Gattungsbuchstaben und Baureihe** (z. B. Einheitsloks **01**, **03**, **41**, **44**, **50**, **86** …), Betriebsnummern oft mit Bindestrich / Prüfziffer je nach Epoche; Tabellen in der Quelle sind **dampflastig**, spätere Triebwagen- und Triebzug-Abschnitte gesondert. |

## Inhalt der Wikipedia-Liste (Struktur)

- **Anmerkungen zu den Tabellen** (Baureihenlogik, Spaltenbedeutung).
- Schwerpunkte: **Dampflokomotiven** (Einheitsbauarten, Länderbahn-Übergänge), weitere Kapitel zu anderen Triebfahrzeugen gemäss Inhaltsverzeichnis der Quelle.

## Review-Hinweis

- Dieselbe Buchstabenfolge **`DR`** wie bei der **DDR-Reichsbahn**; Unterscheidung über **Epoche** (`era`), **Beschreibung**, **Baureihe** und **`country`** (`DE` vs. **`DD`**).
- Nummern-Splits mit [field-parsing-model.md](field-parsing-model.md); bei **Dampf** oft volle Anschrift in einem String → Projekt-Konvention für `type` vs. `number` einhalten.

## Provenienz

Struktur und Baureihen aus der deutschsprachigen Wikipedia «Liste der Lokomotiv- und Triebwagenbaureihen der Deutschen Reichsbahn (1920–1945)»: https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_Deutschen_Reichsbahn_(1920%E2%80%931945)
