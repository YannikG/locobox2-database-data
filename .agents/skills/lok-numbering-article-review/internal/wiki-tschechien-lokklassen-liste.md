# Tschechien (ČD, ČD Cargo, Geschichte ČSD): Plausibilität für Locobox-Artikel

**Baureihen-Gesamtlisten (de.wikipedia):** **ČSD** (1945–1992, Tschechoslowakei) [«Liste der Lokomotiv- und Triebwagenbaureihen der ČSD»](https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CSD); **ČD** (ab 1993, Tschechische Bahnen) [«Liste der Lokomotiv- und Triebwagenbaureihen der ČD»](https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CD). Stichworte und Felder unten; Details in den Originaltabellen (siehe Provenienz).

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **CZ** für heutiges Tschechien; tschechoslowakisches **ČSD**-Vorbild oft **`CS`** (historisch), nach 1993 je Vorbild **CZ** oder **SK**; Exporte (DE, AT, SI, …) nur mit Text/Operator; **nicht** aus Baureihe raten |
| `operator` | **ČD**, **ČD Cargo** (Shop oft «CD» ohne Hächen); historisch **ČSD** (*Československé státní dráhy*, bis 1992; oft «CSD») |
| `electricSystem` | **3 kV DC** dominant; **25 kV 50 Hz**; **Mehrsystem** (z. B. 371, 383); **1,5 kV DC** für Altgrenzverkehr je nach Klasse |

## Baureihen-Stichworte (Loks, unvollständig)

- **Elektro:** **122** (Pendolino-Inland), **140**, **151**, **162 «Persing»**, **363** Mehrsystem, **371**, **380**, **383** Vectron-ähnlich.
- **Diesel:** **714** «Nokia», **721**, **742** «Zamračenka», **749**, **753** «Goggomobil», **771** «Grumpy» (Spitznamen nur zur Erkennung im Text); historische ČSD-Reihen **T 478.1 / T 478.2 / T 478.3** → eigener Abschnitt unten.
- **Triebwagen:** **471** «RegioSpider», **650** «InterPanter», **844** «RegioShark» (Kategorien oft `triebzug`); **M 152.0 / 810** inkl. Beiwagen **Blm** → eigener Abschnitt unten.

## ČSD T 478.1 / T 478.2 / T 478.3 (EDV 751/752/753, 749/750)

Komprimiertes Review-Wissen für Shop-Titel ohne Punkte («**T4782059**») und mit Kryšpín-Punktnotation («**T 478.2059**»).

### T 478.1 und T 478.2 («Bardotka» / «Zamračená»)

| Thema | Fakt für Locobox |
|-------|------------------|
| Rolle | Dieselelektrische Universallok (ČKD Praha), Bo'Bo'; Personenzug (**T 478.1**, Dampfheizung) vs. Güterzugvariante (**T 478.2**, Ballast statt Heizkessel) |
| Historische Nummern | **T 478.1001–1239** (230 Stück); **T 478.2001–2082** (82 Stück) |
| Shop-Kompakt | «**T4782059**» / «**T 478.2059**» = Reihe **T 478.2**, Laufblock **2059** (im Band 2001–2082) |
| Locobox-Split | `type` **`Rh T 478.1`** bzw. **`Rh T 478.2`** (oder ohne `Rh`), `number` = **vierstelliger** Block nach dem Punkt (**1001–1239** bzw. **2001–2082**), z. B. T4782059 → **`2059`**. Nicht nur die letzten drei Ziffern (`059`) |
| EDV ab ca. **1988** | **T 478.1** → **751** (Inventar 001–239); **T 478.2** → **752** (001–082); modernisierte Heizungs-Umbauten oft **749** |
| Spitznamen | «Bardotka», «Zamračená» / «Finstergesicht» → eher Erkennung im Text, nicht zwingend `livery` |
| Provenienz | https://de.wikipedia.org/wiki/%C4%8CSD-Baureihe_T_478.1 |

### T 478.3 («Taucherbrille» / «Brejlovec»)

| Thema | Fakt für Locobox |
|-------|------------------|
| Rolle | Nachfolger-Universallok mit markanten Führerstandsfenstern; 408 Stück |
| Historische Nummern | **T 478.3001–3408** |
| Shop-Kompakt | «**T4783098**» / «**T 478.33098**» → `type` **`Rh T 478.3`**, `number` **`3098`** (vierstellig, inkl. führender **3**) |
| EDV ab ca. **1988** | **753**; modernisiert mit el. Heizung oft **750** (ZSSK/ČD); spätere Umbauten **755**, **753.6/753.7**, SK **756/757** nur bei klarem Text |
| Spitznamen | «Taucherbrille», «Brejlovec» / «Brillenschlange» |
| Provenienz | https://de.wikipedia.org/wiki/%C4%8CSD-Baureihe_T_478.3 |

### Typische Verwechslungen (Finding)

- **T 478.1 vs. .2 vs. .3:** andere Nummernbänder und Optik; Shop-Ziffer nach dem Punkt (**1***/**2***/**3***) entscheidet die Unterreihe.
- **EDV 751/752/753 vs. Kryšpín:** gleiche Familie, andere Epoche/Beschriftung → `type` an Epoche anpassen.
- **Vierstellige `number`:** bei `Rh T 478.n` immer den **vollen** Block nach dem Punkt behalten (`2059`, `3098`), nicht auf `059`/`098` kürzen.

## ČSD M 152.0 (810) und Beiwagen Blm (010)

Komprimiertes Review-Wissen für Shop-Sets «Dieseltriebwagen M 152.0 mit Beiwagen». Nicht mit späteren Umbau-Reihen (**809**, **811–814**, ZSSK **813/913** «Bageta», Marketing **RegioMouse**) verwechseln, solange Text/Epoche **Ursprung / Epoche IV** meint.

### Motorwagen M 152.0 → 810

| Thema | Fakt für Locobox |
|-------|------------------|
| Rolle | Zweiachsiger Dieseltriebwagen (3. Generation ČSD-Schienenbus), Hersteller **Vagonka Tatra Studénka** |
| Technik (kurz) | Achsfolge **1’A’**, dieselhydraulisch (**LIAZ ML 634** + Praga-Getriebe, Bus-Komponenten Karosa ŠM 11), **80 km/h**, LÜP ca. **14 m**, keine Vielfachsteuerung / keine Steuerwagen im Ursprungszustand |
| Spitzname (DE) | «Brotbüchse» (eckiger Wagenkasten) |
| Prototypen | **1973** als **M 151.0001/0002**, **1974** wegen Achslast auf **M 152.0001/0002** umgezeichnet |
| Serie | ab **1975** (mehrere Bauserien bis ca. **1982**); ČSD-Bestand grob **M 152.0001–0678** plus **2** Breitspurwagen |
| Historische Nummer | Schreibweisen **M 152.0xxx** / **M152.0xxx**; Locobox-Split: `type` **`Rh M 152.0`** (oder **`M 152.0`**), `number` = **vierstellige** Laufnummer (**0001–0678**), z. B. M 152.0047 → **`0047`** |
| EDV ab ca. **1988** | Reihe **810**: Inventar **810 001–678** entspricht den alten Laufnummern; Breitspur **M 152.5001/5002** → **810.8** / **810 801/802** |
| Nachfolger | Aufteilung **ČD** / **ŽSR→ZSSK**; Export-nahe Bauart **MÁV Bzmot** (Ungarn) |
| Kategorien | **`triebwagen`**, **`dieseltriebwagen`** (nicht `lokomotive`) |
| `operator` / `country` | Epoche-IV-Ursprung: oft **CSD** / **CS** oder projektüblich **CZ** mit ČSD-Text; Epoche VI **810**: **ČD**/**CZ** oder **ZSSK**/**SK** je Beschriftung |

### Beiwagen Blm → Baafx / 010 / 011

| Thema | Fakt für Locobox |
|-------|------------------|
| Rolle | Beiwagen (Přípojný vůz) zum M 152.0: Aufbau wie Motorwagen, **ohne** Antrieb; an den Enden durchgehende Sitzbank statt Führerstand |
| Einsatz | Bis **zwei** Beiwagen pro Triebwagen; bei den ČSD auch in **lokbespannten** Reisezügen |
| Werks-/Gattung | Tovární typ **8-407.0**; Ursprungsgattung **Blm** |
| Historische Nummern | Prototypen **Blm 25-09 600/601**; Serie **Blm 24-29 000–909** (Lieferjahre ca. **1976–1983** in Inventarblöcken) |
| Umzeichnung | ab **1983** oft **Baafx**; ab **1994** bei ČD Ziffernreihe **010** (neue Inventarnummern, nicht 1:1 die alten 24-29-Nummern); Slowakei **011** (oft mit erhaltenen Inventarnummern), dort war **010** anderweitig belegt |
| Spätere Buchstaben | ČD ab ca. **2001** u. a. **Btax**; Umbau-Unterreihen **012–016** usw. nur bei klarem Textbeleg |
| Locobox Epoche IV | `type` **`Blm`**, `number` = Inventar der Blm-Serie (z. B. **`075`** für Blm 24-29 075), Kategorie **`wagen`**, `electricSystem` typisch **`Unbekannt`** |
| Locobox später | `type` **`Baafx`** / **`010`** / **`Btax`** nur wenn Epoche/Beschriftung das klar zeigen; nicht aus «Blm»-Shoptext raten |

### Roco- / Shop-Sets «mit Beiwagen»

Shop-PDPs bündeln oft **einen** Motorwagen + **einen** Beiwagen unter **einer** Art.-Nr. Locobox modelliert **zwei** Fahrzeuge:

1. Motorwagen-Datei = Shop-SKU (`articleNumber` z. B. `70373`): `Rh M 152.0` + Laufnummer, Kategorien Triebwagen, `setNumber` = dieselbe SKU.
2. Beiwagen-Datei = **`{sku}-blm`** (z. B. `70373-blm.json`): `Blm` + Beiwagen-Nummer, Kategorie `wagen`, `setNumber` = Shop-SKU, `source.url` darf auf die Set-PDP zeigen, `notes` = Beiwagen-Teil.

**Nicht** Auto-Fix: Beiwagen-Gattung und -Nummer im Motorwagen-`type` belassen («… mit Beiwagen Blm …»). Analog/Digital/AC-Schwestern derselben Set-Familie gleich behandeln.

### Typische Verwechslungen (Finding)

- **810** vs. **M 152.0**: gleiche Fahrzeugfamilie, andere Epoche/Beschriftung → `type` an Epoche anpassen, nicht mischen.
- **809 / 811–814 / 813+913**: Umbauten oder Doppeleinheiten, andere Typ-/Nummernlogik.
- **M 152.5 / 810.8**: Breitspur (1520 mm), selten in H0-Neuheiten.
- Einzel-Beiwagen-SKU im Shop (z. B. Roco **74241** «Baafx») ist **kein** Set: eine Datei, kein `{sku}-blm`-Zwilling nötig.

## Nachbarländer (vorsichtig)

- Viele **Škoda**- und **ČSD**-Baumuster liefen auch in **Slowenien** (JŽ/SŽ), **Slowakei** ([wiki-slowakei-zssk-loks-liste.md](wiki-slowakei-zssk-loks-liste.md)), teils **Österreich** und **Ungarn**. Plausibilität: ja; `country` automatisch ändern: **nein**, ohne Textbeleg.

## Split `type` / `number`

- Häufig «**363 129-4**»-Muster: dreistellige BR + Nummer mit Prüfziffer → Standard-Split.
- **M 152.0xxx** → `Rh M 152.0` / `xxxx` (vier Stellen, führende Nullen behalten).
- **T 478.nxxx** / Shop **T478nxxx** (ohne Punkte) → `Rh T 478.n` / `nxxx` (vier Stellen; siehe Abschnitt T 478.1/.2/.3).
- **Blm 24-29 xxx** (Epoche IV) → `Blm` / `xxx` (Inventar 000–909); nicht fälschlich als **010**-Inventar der ČD-Neunummerierung lesen.

## Review-Hinweis

- Stromsystem (3 kV vs. 25 kV vs. MS) vs. Baureihe; Lok vs. Triebzug-Kategorie → **Finding**.
- Set «mit Beiwagen» ohne zweite Datei oder mit gemischtem `type` → **Finding** (siehe Abschnitt M 152.0 / Blm).

## Provenienz

**Primär:**

- Tschechoslowakei **ČSD:** https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CSD  
- Tschechische Bahnen **ČD:** https://de.wikipedia.org/wiki/Liste_der_Lokomotiv-_und_Triebwagenbaureihen_der_%C4%8CD  
- **M 152.0 / 810 (inkl. Beiwagen-Hinweis):** https://de.wikipedia.org/wiki/%C4%8CSD-Baureihe_M_152.0  
- **T 478.1 / T 478.2 (751/752, 749):** https://de.wikipedia.org/wiki/%C4%8CSD-Baureihe_T_478.1  
- **T 478.3 (753/750):** https://de.wikipedia.org/wiki/%C4%8CSD-Baureihe_T_478.3  

**Vertiefung Beiwagen / Umbauten (optional):**

- Přípojné vozy **010–016 / 011** (Blm → Baafx → Btax): https://www.vlaky.net/zeleznice/spravy/002328-Pripojne-vozy-na-nasich-kolejich-rady-010-016-CD-011-ZSSK/  
- Motorwagen-Serie **řada 810**: https://www.vlaky.net/zeleznice/spravy/002160-Motorove-vozy-na-nasich-kolejich-rada-810/  
- Englisch Kurzüberblick: https://en.wikipedia.org/wiki/%C4%8CSD_Class_M_152.0  

Inhalt dieser Datei **komprimiert offline**.
