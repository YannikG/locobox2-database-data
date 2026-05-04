# Luxemburg (CFL): Plausibilität für Locobox-Artikel (Lokomotiven)

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **LU** |
| `operator` | **CFL** (*Société nationale des chemins de fer luxembourgeois*); Güter oft **CFL cargo**; grenzüberschreitend **SNCF**, **DB**, **Lineas** im Text erwähnen |
| `electricSystem` | **25 kV AC** (Hauptstrecken); **3 kV DC** und **15 kV AC** an Drehstrom-Grenzen je nach Linie (Modelltext «Arlberg», «Metz», «Trier» lesen) |
| `categories` | Kleines Land, aber volle Palette: **elektrolokomotive** dominant modern; **diesellokomotive**; historisch **dampflokomotive** (Museum) |

## Bestand-Logik (Stichworte, nicht vollständig)

| Antrieb | Typische Baureihen / Kontext |
|---------|------------------------------|
| Elektro | **3000** (Altbau), **4000** (TRAXX), **13xx**-Umfeld, moderne Mehrsysteme für Güter und Personen |
| Diesel-elektrisch | Wenige, oft Rangier oder historische Importe |
| Diesel | Rangier und leichte Streckendiesel |
| Dampf | Museumsstücke, selten Serienmodell |
| Normalspur | praktisch alle H0-Modelle; Schmalspur aussergewöhnlich |

## Split `type` / `number`

- Wie benachbarte Bahnen oft «**4008**» oder «**13 001**»-Schreibweise; BR in `type`, Nummer in `number`, wenn der Import zusammengeklebt ist.

## Grenzfälle

- **Grenzverkehr:** französische oder belgische Nummern im Fliesstext → `country` nicht ohne Text auf FR/BE ändern.
- **CFL-Doppelstock:** Triebzug-Kategorie vs. Lok.

## Review-Hinweis

- Stromsystem (25 kV vs. 3 kV vs. 15 kV) widerspricht Karte oder Bild → **Finding**.

## Provenienz

Kategorienbaum «Locomotives of Luxembourg» (englische Wikipedia) diente als Antriebs-Checkliste; Inhalt hier **komprimiert offline**.
