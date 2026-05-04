# Schweden: Plausibilität für Locobox-Artikel (Lokomotiven)

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **SE** |
| `operator` | **SJ** (Personen), **Green Cargo** (Güter), **Hector Rail**, **Tågab**, **Snälltåget** je nach Epoche; historisch einheitlich **SJ**-Vorgänger |
| `electricSystem` | **15 kV 16,7 Hz AC** (Normalspur-Hauptnetz); Mehrsystem-Loks für Grenze (D, DK) im Text prüfen |
| `categories` | Viele **elektrolokomotive**; Güter **diesellokomotive** (T44, T66f); Dampf meist Museum; **triebzug** für X2000, Regina, X55 usw. |

## Antriebs-Überblick (für Kategorie-Check)

| Antrieb | Einordnung (Stichworte) |
|---------|-------------------------|
| Dampf | Museums- und Sonderfahrten; historische SJ- und Privatbahn-Loks |
| Elektrolok | Grosse Gruppe: **Rc**, **Rd**, **Rb**, **Ae**-Umfeld, **IORE** (Erz, oft Grenze **NO**), **Traxx**-Derivate |
| Diesellok | **T44**, **T66**, **TmZ**-Rangier; Import **Euro**-Diesel möglich |
| Diesel-elektrisch | Einige US-/Import-Bauarten in Güterdienst (Epoche beachten) |
| Triebzug | **X2** (X2000), **X40**, **X55** (Snabbtåg), **Regina**-Familien |

## Baureihen- und Nummernlogik (Review)

- **Rc / Rd:** häufig «**Rc6 1392**» oder nummerisch ähnlich; BR-Buchstaben in `type`, Ziffernblock in `number`, wenn Shop zusammenklebt.
- **Green Cargo:** oft TRAXX / **Transmontana**-Umfeld; nicht mit SJ-Personenfarbe verwechseln.
- **IORE:** typischerweise **NO**-Grenzbezug prüfen, wenn Text «Kiruna» / «Malmbanan»; reines SE-Modell trotzdem möglich.

## Grenzfälle

- **Normalspur vs. Schmalspur:** Museums-Schmalspur separat (H0e etc.).
- **«Individual locomotives»**-Fall: Einzelstück mit Name → `livery` oder `description`, EVN trotzdem splitten wenn vorhanden.

## Review-Hinweis

- Kategorie Elektro, aber Diesellok-BR im `type`, oder umgekehrt → **Finding**.

## Provenienz

Kategorienbaum «Locomotives of Sweden» (englische Wikipedia) diente als Checkliste für Untergliederung Dampf / Elektro / Diesel / Diesel-elektrisch / Normalspur / SJ / Green Cargo; Inhalt hier **komprimiert offline** nutzbar.
