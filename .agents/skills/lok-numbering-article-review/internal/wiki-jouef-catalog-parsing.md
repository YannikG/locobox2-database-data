# Jouef: Katalog-Parsing und Review-Fallen

Gilt für Catalog-only Importe (`uv run locobox catalog extract --source jouef`) und anschliessendes Loknummer-Review unter `articles/jouef/`. Shop-PDP ist Stub; Belege kommen aus Hornby/Jouef-Katalog-PDF (`pdftotext`) und ggf. Shop-/Händlerseiten.

## Artikelnummern

| Form | Bedeutung |
|------|-----------|
| `HJ####` | Analog / ohne Werk-Sound |
| `HJ####S` | gleiche Vorbildvariante, **DC-Digital** + `features: ["sound"]` |
| `variantGroup` | Basis ohne `S` (z. B. `HJ2447`) |

Schwesterregel: bei Korrektur an einem Mitglied der Gruppe denselben `type` / `number` / `livery` / `era` / `operator` / `categories` auf die Schwester anwenden, **Stromsystem und Sound** nicht spiegeln (Analog bleibt Analog).

## PDF-Mehrspalten-Fallen (häufig)

Neuheiten-/Indexseiten setzen **drei SKUs nebeneinander**. `pdftotext` und naive Zeilenparser mischen oft:

- Titel/Beschreibung der **Nachbarspalte** an die falsche SKU
- Indexzeile nur mit SKU, ohne Text → Stub-Beschreibung (`"HJ2447"`)
- TGV-Coffret-Text landet auf Dampf-/Dieselloks und umgekehrt

**Review-Pflicht:** Jede verdächtige Datei gegen die **SKU-Zeile plus die darunter liegende Produktzeile derselben Spalte** prüfen (oder gegen fr.jouef.com / uk.jouef.com / Händler). Nicht den Fliesstext der Nachbarspalte übernehmen.

Typische Fehlzuordnungen aus dem 2025er Index (korrigierte Lesart):

| SKU | Richtig (Kurz) | Häufiger Fehler |
|-----|----------------|-----------------|
| HJ2432 | 141 R **420**, Kohletender, ép. V | Nummer/Livery von 1244 |
| HJ2433 | 141 R **1244**, Fuel-Tender, ép. V | fälschlich TGV Sud-Est |
| HJ2441 | BB **666442**, Diesel, ép. VI | fälschlich TGV |
| HJ2442 | BB **66400** FRET grün, ép. VI | fälschlich TGV |
| HJ2447 | BB **167424** Multiservice, ép. VI | leere BB 67400 |
| HJ2449 | BB **12013** Elektro, ép. III | fälschlich BB 67400 Diesel |
| HJ2429 | RGP II **X 2719**, ép. IV | Nummer/Epoche von HJ2420 |

## SNCF-Felder (Jouef-Konvention)

Siehe [reference-sncf-type-number.md](../reference-sncf-type-number.md) und [wiki-sncf-loks-liste.md](wiki-sncf-loks-liste.md).

Zusätzlich im Jouef-Katalog:

- UIC-ähnliche Sechserblöcke (`467471`, `567556`, `167424`, `436300`) bleiben **volle Anschrift** in `number`; `type` = Serie (`BB 67400`, `BB 36000`, …).
- Serie **BB 67400** umfasst u. a. Laufnummern **67401–67632** → `type` immer `BB 67400`, nicht `BB 67600`.
- Unterfamilien **BB 66400** / **BB 66600** dürfen als `type` stehen, wenn der Katalog die Unterserie nennt; sonst Familie `BB 66000`.
- TGV-Coffrets: `categories: ["triebzug"]`, `number` = Ramennummer wenn genannt (z. B. inaugurale **17**), Lack kurz in `livery`.
- RGP I/II: `type` `RGP I` / `RGP II`, `number` z. B. `X 2719`, Kategorien `triebwagen` + `dieseltriebwagen`.
- Privat-/Tochter-Operatoren aus Katalogzeile: **COLAS RAIL**, **Europoorte**, **Millet Rail**, **Akiem**, **SNCF Infra** (nicht alles auf `SNCF` glätten).

## Decoder / Strom

Aktuelle H0-Triebfahrzeuge: `decoderInterface` = **`NEM 660 (21MTC)`** (Kataloglegende «Mit Digitalschnittstelle nach NEM 660 (21-pin MTC)»). Nicht `Unbekannt` lassen, wenn der Katalog die 21MTC-Legende für die Serie führt. `electricSystem` nur Analog vs. Sound-`S`, nicht Vorbild-kV.

## Provenienz

Jouef/Hornby Neuheiten 2025 und Catalogue 2026 (PDF/`pdftotext`), Abgleich mit fr.jouef.com / uk.jouef.com und lestrainsjouef-Teilelisten; Locobox-SNCF-Split wie Roco-Importe.
