# Italien (FS, Trenitalia, Regionalbahnen, Italo): Plausibilität für Locobox-Artikel

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **IT**; Sonderfälle Museumsbahnen im Ausland mit italienischem Vorbild im Text klären |
| `operator` | **FS** / **Trenitalia** (Personenfern), **Mercitalia** (Güter), **Italo** (NTV, Hochgeschwindigkeit), **Ferrovie Nord Milano (FNM)**, historisch **SFMT** / **FS**-Vorgänger |
| `categories` | `triebzug` bei **Italo** / **Frecciarossa**- und **Pendolino**-Umfeld; `elektrolokomotive` bei klassischen E-Loks; Schmalspur oft eigene Museums-/Regionalbahn |

## Stromsysteme (für `electricSystem` und Textabgleich)

- **3 kV DC:** Hauptnetz historisch und heute noch dominant im Norden und auf vielen Hauptstrecken.
- **25 kV 50 Hz AC:** Hochgeschwindigkeit und modern ausgebaute Strecken.
- **Mehrsystem:** Viele moderne Fern- und Güterloks (Wechsel zwischen 3 kV und 25 kV).
- **Gleichstrom-Lokalnetze:** ältere S-Bahn-/Vorortstrecken (Modelltext genau lesen).

## Baureihen-Stichworte (nicht vollständig)

- **Elektro-Loks:** Reihen **E.4xx**-Schema (historisch), **E.6xx**-Umfeld, modern **E.4xx** TRAXX/Vectron-Derivate je nach Epoche.
- **Diesel:** **D.4xx**, Rangier **D.2xx**-Umfeld (stark vereinfacht; immer Text prüfen).
- **Triebzüge:** **Vivalto**, **Minuetto**, **Swing**, **Coradia**-Familien; **Italo** als eigenes Marken-Design (nicht FS).
- **Schmalspur:** Eigene Baureihenlogik (Rittner Bahn, Vesuv, …) → `scale` / Text «950 mm» etc. prüfen.

## Split `type` / `number`

- Italienische Beschriftung oft «**E 464 321**» oder «**E464 321**»; einheitlich **BR in `type`**, Rest in `number`, wenn der Import nicht schon getrennt liefert.
- **Italo / Zugname:** Zug-/Marketingname → `livery` oder Fliesstext, nicht in `number` erzwingen.

## Grenzfälle

- **FS vs. Italo:** gleiche Spannungssysteme möglich, Operator muss stimmen.
- **Historische Gesellschaft** (SFM, SEPSA) nur wenn Epoche und Text das tragen.

## Review-Hinweis

- Widerspruch Stromsystem (3 kV vs. 25 kV) vs. Baureihe, oder Triebzug-Kategorie vs. Lok-Felder → **Finding**.

## Provenienz

Kompakt aus der deutschsprachigen Wikipedia-Liste «Liste der italienischen Lokomotiven und Triebwagen» (Gliederung nach Gesellschaften und Antrieb).
