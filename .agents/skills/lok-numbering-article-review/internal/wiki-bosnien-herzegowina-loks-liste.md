# Bosnien und Herzegowina: Plausibilität für Locobox-Artikel

Zwei Eisenbahnunternehmen nach dem Dayton-Umfeld: **ŽFBH** (*Željeznice Federacije Bosne i Hercegovine*, Föderation) und **ŽRS** (*Željeznice Republike Srpske*). Einstieg deutsch: [«Željeznice Federacije Bosne i Hercegovine»](https://de.wikipedia.org/wiki/%C5%BDeljeznice_Federacije_Bosne_i_Hercegovine) bzw. [«Željeznice Republike Srpske»](https://de.wikipedia.org/wiki/%C5%BDeljeznice_Republike_Srpske) (siehe Provenienz). Selten in Westeuropa-Shops; bei Balkan-/Ex-Jugoslawien-Importen und Grenzverkehr mit HR/RS/ME prüfen.

## Locobox-Validierung (Pflichtcheck)

| Feld | Erwartung |
|------|-----------|
| `country` | **BA** |
| `operator` | **ŽFBH** oder **ŽRS** (Locobox oft ohne Diakritika: **ZFBH** / **ZRS**); historische **JŽ** nur bei klarem Epoche-/Textbezug |
| `electricSystem` | Vorbild Mischlage (u. a. **25 kV AC**, ältere DC-Inseln); Modell-H0 wie üblich Analog/Digital am Modell |
| `categories` | Lok vs. Wagen; Schmalspur **760 mm** (bosnische Spur) → `scale` oft **`H0e`**, nicht mit Normalspur vermischen |

## Operator-Anker

| Text / Shop | Locobox `operator` | `country` |
|-------------|--------------------|-----------|
| ŽFBH, ZFBH, Railways of the Federation | **ŽFBH** (oder **ZFBH**) | BA |
| ŽRS, ZRS, Republika Srpska Railways | **ŽRS** (oder **ZRS**) | BA |
| JŽ / Jugoslovenske železnice (historisch) | **JŽ** | nur mit Epoche/Text; `country` oft historisch, nicht blind **BA** |

## Baureihen-Stichworte (unvollständig)

- **Normalspur:** ex-JŽ-Diesel- und Elektrolokfamilien (u. a. «Kennwort»-Serien, GM/EMD-Ableger, Škoda/Končar-Umfeld) nur mit Textbeleg; Nummernschemata weichen von CFR/BDZ ab.
- **Schmalspur 760 mm:** Museums- und Touristikstrecken; Modell oft **H0e**. Nicht mit RhB/MGB-Naming vermengen → [wiki-rhb-mgb-schmalspur-naming.md](wiki-rhb-mgb-schmalspur-naming.md) nur für CH/AT-Vorbilder.

## Split `type` / `number`

- Keine CFR-**060-EA**-Logik auf BA-Artikel übertragen.
- EVN mit Landescode **BA** bzw. alter JŽ-Logik: nur splitten, wenn Baureihe und Laufnummer klar getrennt sind.

## Grenzfälle

- **Zwei Betreiber im Land:** Text entscheidet ŽFBH vs. ŽRS; nicht «Bosnien» als Operator.
- **Grenzverkehr HR/RS/ME:** `country` nach Lack/Betreiber im Text.
- **Schmalspur vs. Regelspur:** `scale` und Kategorie gegen Text; Finding bei Widerspruch.

## Review-Hinweis

- `country` **HR**, **RS** oder **BA** verwechseln → Finding.
- Operator **CFR**/**BDZ** auf BA-Vorbild → Finding.

## Provenienz

**ŽFBH:** https://de.wikipedia.org/wiki/%C5%BDeljeznice_Federacije_Bosne_i_Hercegovine

**ŽRS:** https://de.wikipedia.org/wiki/%C5%BDeljeznice_Republike_Srpske

**Kontext (englisch, Überblick):** https://en.wikipedia.org/wiki/Rail_transport_in_Bosnia_and_Herzegovina

Inhalt dieser Datei **komprimiert offline**.
