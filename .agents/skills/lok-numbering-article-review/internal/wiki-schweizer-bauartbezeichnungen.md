# Auszug: Bauartbezeichnungen der Schweizer Lokomotiven und Triebwagen

## Zeitachse

- **Bis 1887:** verschiedene Klassenbuchstaben (z. B. A–F: Schnellzug-, Personenzug-, Güterzuglok usw.).
- **1887–1901:** Klassen A–H mit Achszahl und Index (E = Engerth-Tender, T = Schlepptender, fehlend = Tenderlok).
- **Ab 1902 (SBB-Gründung):** System für Lokomotiven und Triebwagen bis **1989** weitgehend unverändert; letzte grössere Anpassung Privatbahnen-Verzeichnis 1968.
- **Wagen:** ab 1966 sukzessive UIC-Bezeichnung.
- **Triebfahrzeuge:** ab **1989** neues System (Serienbezeichnung + Bauartnummer + Fahrzeugnummer); zuerst neue Fahrzeuge (erste: SBB Re 450 000), dann Normalspur-Privatbahnen; Schmalspur grösstenteils alte Serienbezeichnungen.

## System 1902–1989: Lokomotiven (Schema)

Aufbau: **Serienbuchstabe(n)** + **Traktion** (Kleinbuchstabe) + **Triebachsen** / **Gesamtachsen** + optional **römische Zahl** (Serie).

| Teil | Werte (Auszug) |
|------|----------------|
| Serienbuchstabe Lok | A vmax >80 Normalspur, B 70–80, C 60–65, D 45–55, E Rangier/Dampf-Tenderlok, G Schmalspur Adhäsion, H Zahnrad, R „rapid“ erhöhte Kurvengeschwindigkeit, vmax ≥110 Normalspur, T Traktor/feuerlose Dampflok |
| Traktion | fehlend = Dampf; **e** elektrisch; **m** thermisch (Diesel/Gasturbine); **a** Akku; Kombinationen möglich (z. B. Gea, Tem); Zahnrad: **h**-Regeln wie im Vollartikel |
| Zahlen | erste Zahl = Triebachsen, zweite = alle Achsen; Dampf-Mallet etc. Sonderformen |
| Index | römisch = Bauserie (z. B. Re 4/4 **II**) |

Beispiel: **Re 4/4 II** = R + e + 4 Triebachsen + 4 Achsen, zweite Serie.

**Re 10/10** ist **keine** Baureihe, sondern die Betriebsbezeichnung der Doppeltraktion **Re 4/4 III + Re 6/6** (zehn angetriebene Achsen, oft Gotthard-Güterzug). Roco-Sets (z. B. **71409**) → **zwei** Artikeldateien mit `setNumber`, nicht `type` `Re 10/10`; siehe [field-parsing-model.md](field-parsing-model.md) → Sets.

## System 1902–1989: Triebwagen (Schema)

Ähnlich: Grossbuchstaben für Wagenklassen (A Erste, B Zweite, D Gepäck, Z Post, R erhöhte Kurvengeschwindigkeit, Kombinationen wie ABDe), Traktion, Achszahlen, Index. Spezialfälle TEE (RAm/RAe) und Zahnrad (**h** vor Antriebskennzeichen bei reinem Zahnradfahrzeug).

## Ab 1989: UIC-kompatible 12-stellige Darstellung

- Serienbezeichnung (**Re**, **RABDe**, …) bleibt **vorangestellt**.
- Nummer: zwei **Dreiergruppen** + **Prüfziffer** mit Bindestrich, z. B. `Re 460 003-7` (Serie 460, Laufnummer, Check).
- In der 12-stelligen Logik: Stellen 1–2 Fahrzeugtyp/Traktion (Auszug): 00 Dampf/Museum, 01 E-Lok, 02 elektrischer Triebwagen/-zug, 03 Diesellok, 07 Traktor, 08 Schneepflug, 09 Sonder; 1x Schmalspur; 2x Traktoren; 3/4 E-Loks nach Achsen; 5x Triebwagen/Triebzüge (50 Fern, 51 S-Bahn, …); 6x E-Loks >4 Triebachsen; 8 Dieselloks (2. Ziffer oft Triebachsen); 9 E-Rangierloks.
- Stellen **3–4:** Eigentümergesellschaft / Land (Schweiz oft **85**); SBB grosse Nummernkreise, BLS 5x, weitere Codes 60–89 für Regionalbahnen, Private, Post, usw. (Detail im Vollartikel).
- Stellen **5–6:** laufende Nummer (inkl. 000/001 je nach Bahn).
- **Triebzüge SBB:** 5. Stelle der 12-stelligen Nummer kann **Wageneinheit** zählen (0 = Gesamtzug, 1 vorderer Endwagen, …); Beispielkette RAe TEE II im Originalartikel.
- **Triebzüge BLS (MUTZ):** Zähler teils über **9.** Stelle der 12-stelligen Nummer, damit gleiche Prüfziffer wie Kurzform.
- **Umnummerierung / Ausgleichsziffer:** z. B. BLS Re 465: alte interne Zwölfsteller vs ab 2009 TSI; fünfte Stelle kann Ausgleich für gleiche Prüfziffer wie 7-stellige Nummer dienen.

## Review-Hinweis

CH-Modell: oft **Kurzname + 6 Ziffern + Prüfziffer**. 12-stellige volle Nummer nur grob prüfen; Sonder- und Historikfälle ohne weitere Quelle als **unklar** markieren.

### Re 420 / Re 421 (SBB / SBB Cargo)

Nach dem System ab 1989 heisst die frühere **Re 4/4 II** in der Kurzform **`Re 420`** (Personen-/Cargo-Stamm) bzw. **`Re 421`** (Umbauten mit DB-Zulassung, SBB Cargo, Nummernkreis typisch **421 371–397**).

| Shop-/Import | Locobox |
|--------------|---------|
| Titel «Elektrolokomotive **421 389-8**, SBB Cargo» (oft ohne «Re») | `type` **`Re 421`**, `number` **`389-8`** |
| Titel «… **420** …» analog | `type` **`Re 420`**, `number` = Ordnungsblock |

**Nicht** nur `421` / `420` in `model.type` belassen: Repo-Konvention und Suche erwarten das Präfix **`Re`** (vgl. bestehende `Re 420`-Artikel). Altbezeichnung **Re 4/4 II** darf in der `description` stehen, gehört aber nicht allein in `type`, wenn die Betriebsnummer schon im 421-/420-Schema ist.

Beleg Vorbild: [SBB Re 4/4 II](https://de.wikipedia.org/wiki/SBB_Re_4/4_II) (Re 420/421, Cargo 421 371–397).
