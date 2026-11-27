# Märklin Produktdatenbank: Import-Artefakte und Review

Komprimiertes Wissen für **Loknummerierung und Plausibilität** nach Import aus `www.maerklin.de` (Produktdatenbank, gleiche HTML-Form wie Trix). **Import-Workflow:** Skill [locobox-import](../../locobox-import/SKILL.md). **Autofix:** `scripts/autofix_trix_shop_import.py` (gilt für Trix und Märklin), danach `scripts/autofix_maerklin_shop_import.py` (Klassen-Präfix im Typ, z. B. «Nahverkehrs-Dieseltriebwagen LINT 41» → `LINT 41`).

## Kontext

- PDP: `https://www.maerklin.de/de/produkte/details/article/{nr}`
- UVP kommt **nicht** aus dem PDP, sondern aus dem **Katalog-Preisindex** (Queue/`approved.txt` → `uvp_amount` beim Parse).
- H1 ist oft nur die Produktklasse (`Elektrolokomotive`). Baureihe und EVU stehen in **`Vorbild:`**.

## Typische Artefakte

| Artefakt | Bedeutung | Review / Autofix |
|----------|-----------|------------------|
| H1 = nur `Dampf-/Diesel-/Elektrolokomotive` | Shop-Klassenwort | Typ aus erster Vorbild-Zeile (`Baureihe` / `Serie` / `Reihe` / `Typ`); Autofix-Skript |
| `( NS )` mit Spaces in Klammern | Operator-Code | Parser: `\(\s*OP\s*\)`; sonst Finding |
| `type` / `description` = `Suchen` | Fetch hat Suchseite statt PDP geliefert | HTML verwerfen, aus Katalogtext nachziehen oder erneut fetch |
| Langer Marketing-H1 ohne Baureihe | z. B. «US-Güterzug-Dampflokomotive mit Öl-Schlepptender» | Klasse aus Vorbild (`Class 3900`, `Challenger` → Livery) |
| `Rh` + kurze Ziffern | nur **NL/NS**; ÖBB `Reihe 2016` nicht als Rh | Autofix: Rh nur bei 1–3 Ziffern und NL-Kontext |
| Anführungszeichen `„…“` / `"…"` im Vorbild | Spitzname / Werbefolierung | nach `model.livery`, nicht im Typ lassen |

## Katalog-Preisindex (UVP)

Neuheiten-PDFs liefern unterschiedliche Index-Zeilen. Parser in `tools/cli/.../maerklin/catalog.py`:

| Jahrgang (typisch) | Beispiel | Hinweis |
|--------------------|----------|---------|
| ~2015 | `36623  41  € 199,95*` | Euro-Zeichen, Cent, optional `*` |
| ~2015 | `36429  36,185  € 229,95*` | Mehrseitige Seite `36,185` |
| ~2015 | `37985  U4  € 449,95*` | Seite `U4` |
| ~2016–2019 | `37008  10  289,99` | Cent ohne Euro-Zeichen |
| ~2020+ | `39716  76  750,–` | En-Dash / Minus nach Komma |

Nach Parse: Artikel mit `uvp.amount == 0` gegen alle `.tmp/…/nh*.txt` Indexe backfillen (`articles patch`), bevor Phase 2 startet.

## Operator aus Vorbild

Reihenfolge im Parser: US-Namensrouten → Klammer-Codes → Freitext-EVU (Hector Rail, MRCE, KPEV, K.Bay.Sts.B., UP, NSB, …) → generische DB/SBB/ÖBB.

Privat-/Leasing-EVU ohne Klammer und ohne Map-Eintrag → Pass-1-Finding, nicht raten.

## Kategorien

Parent `lokomotive` plus `dampf-/diesel-/elektrolokomotive` aus Roh-Typ oder Vorbild-Antriebswort. Autofix-Skript setzt das, wenn der Roh-Typ noch das Klassenwort enthält.

## Triebwagen / Triebzüge

Parser setzt `triebwagen`/`triebzug` plus `dieseltriebwagen`/`elektrotriebwagen`/`akkutriebwagen` aus Titel und Vorbild; Parent `lokomotive` bleibt wie bei den bisherigen Märklin-Artikeln. UVP fehlt auf PDPs ausverkaufter Artikel (`uvp.amount` 0). Release-Jahr = erster Katalog unter «Veröffentlichungen» auf dem PDP.

## Bewusst ausserhalb dieses Skills

- Allowlist-Host `www.maerklin.de` (eigener Maintainer-PR, nur `config/allowed-source-hosts.json`)
- Katalog vs. Shop-Vollständigkeit, `releaseDate` / Kampagnen-Tags

## Provenienz

Aus Locobox-Import **Märklin H0 Neuheiten 2015–2026** (`maerklin-neuheiten-2015` … `2026`): Preisindex-Formate, generische H1, Suchseiten-HTML, Operator-Spaces, Autofix über `autofix_trix_shop_import.py`.
