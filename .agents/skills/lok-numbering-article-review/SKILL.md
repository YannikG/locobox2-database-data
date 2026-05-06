---
name: lok-numbering-article-review
description: >-
  Two-phase Locobox article JSON review plus optional auto-fix: (0) on request,
  apply whitelisted splits, livery/era fixes, and same-rule fixes to sibling
  variant articles when present in repo (per manufacturer rules in skill docs);
  country only when unambiguous. (1) full pass with findings, (2) one file at a
  time user resolves (skip / ignore). Read-only unless auto-fix or explicit edit
  order. Re-review of ignored items only when user explicitly asks. Use for
  Loknummer review or when this skill is attached.
disable-model-invocation: true
---

# Loknummerierung: Parsing, Split, Plausibilität (zwei Phasen)

## Hauptziel

1. **Parsen und splitten:** Aus `model.type` (und bei Bedarf `description`, `source.url`, `model.number`) Baureihe/Reihe vs laufende Nummer ableiten.
2. **Plausibilität:** Abgleich mit Operator, Land, **Stromsystem** (`model.electricSystem` vs. Beschreibung und vs. **Schwester-Varianten** derselben Baureihe laut Hersteller-Logik, siehe unten), **`scale`** (Schema: u. a. `H0`, nicht `h0`), **Kategorien** vs. Baureihe (z. B. Diesellok vs. `elektrolokomotive`), Fliesstext, internen Kurzreferenzen (**EVN vs. Wagen** nicht verwechseln, siehe `reference-evn-uic.md`). Optional: **`id`** / `articleNumber`, **`setNumber`**, **`decoderInterface`** nur bei Widerspruch zur Beschreibung oder offensichtlichem Parserfehler.
3. **Livery und Sondernamen:** Beim Splitten prüfen, ob neben Baureihe und Nummer noch **Taufname, Sonderfolierung, Piercer-/Marketing- oder Zug-/Produktname** (oft in Anführungszeichen im Roh-Import) vorkam. Wenn ja: **Finding**, falls `model.livery` noch generisch (`SBB`, `OBB`, …), `null` ist oder ein **Import-Mischstring** (z. B. halber Satz statt Lackname). Empfehlung: kurz und konkret in **`model.livery`** ablegen, Details optional im Fliesstext; nicht stillschweigend verlieren. Details: [internal/field-parsing-model.md](internal/field-parsing-model.md) («Livery nach Split»).

Ausführung in **zwei Phasen** (Pass 1, Phase 2), optional davor oder dazwischen **Auto-Fix** (siehe unten). **Standard:** keine JSON-Schreibzugriffe ohne expliziten Auto-Fix oder andere Schreibbeauftragung.

## Hard rules

1. **Scope:** Nur geänderte oder vom User genannte `articles/**/*.json` auf dem **aktuellen Branch** (Git wie unten), oder nur genannte Pfade unter `articles/`.
2. **Read-only:** Pass 1 und Phase 2 sind inhaltlich **Review-first**. Artikel-JSON **nur** schreiben, wenn (a) der User **Auto-Fix** ausdrücklich wünscht (siehe Abschnitt «Auto-Fix») und nur gemäss der dortigen Allowlist, oder (b) der User eine **konkrete** Änderung pro Datei oder global beauftragt (dann ausserhalb dieses Skills die üblichen Projektregeln).
3. **Ehrlichkeit:** Mehrere Lesarten klar trennen. Nicht raten ohne Kennzeichnung. **Auto-Fix** kein Raten: nur Regeln aus der Allowlist, sonst Finding und Datei unverändert lassen.

## Git: welche JSON-Dateien

Vor dem Review (Repo-Root). **Fallback** nutzen, weil viele Repos `master` statt `main` führen:

```bash
git fetch origin main 2>/dev/null || true
git fetch origin master 2>/dev/null || true
BASE=$(
  git merge-base HEAD origin/main 2>/dev/null \
  || git merge-base HEAD main 2>/dev/null \
  || git merge-base HEAD origin/master 2>/dev/null \
  || git merge-base HEAD master 2>/dev/null \
  || echo ""
)
if [ -n "$BASE" ]; then
  git diff --name-only "$BASE"...HEAD -- 'articles/**/*.json'
else
  git diff --name-only HEAD -- 'articles/**/*.json'
fi
```

- User nennt Pfade: nur diese Dateien.
- Keine Diff-Dateien: User fragen (gesamter `articles/`-Baum oder Teilpfade).

## Auto-Fix (optional, mechanisch)

**Auslöser:** Nur wenn der User das klar verlangt (z. B. «mit Auto-Fix», «Auto-Fix auf dem Scope», «bekannte Parserfehler automatisch»). Ohne diesen Wunsch **keinen** Auto-Fix ausführen.

**Reihenfolge:** Scope wie unter «Git» ermitteln → **Arbeitsatz erweitern** (Schwesterartikel, siehe unten) → **Auto-Fix-Pass** auf dem erweiterten Satz → **Pass 1** (Findings; bereits korrigierte Felder kurz als «Auto-Fix erledigt» markieren) → Phase 2 unverändert.

**Pflichtprotokoll:** Für jede geänderte Datei eine Zeile im Chat (oder kurze Tabelle): `Pfad`, `Feld`, `alt → neu`. Keine stillen Massenänderungen.

### Schwesterartikel (Variantengruppen, herstellerneutral)

Vor dem eigentlichen Auto-Fix den **Arbeitsatz** aus dem Git-Scope wie folgt **ergänzen**:

1. **Variantengruppe definieren** über `manufacturer`, `articleNumber` / `id` und **im Projekt dokumentierte Regeln** (z. B. in [field-parsing-model.md](internal/field-parsing-model.md) oder einem `internal/wiki-*.md` zum Hersteller): welche Artikel gelten als **dieselbe Modellfamilie** (Analog/Digital/AC, Sonderlack, Set-Teil A/B)?
2. **Alle im Repo vorhandenen** JSON-Dateien derselben Gruppe unter `articles/<hersteller>/` in den Auto-Fix-Arbeitsatz aufnehmen, **auch wenn** sie nicht im Git-Diff stehen, sobald mindestens **ein** Gruppenmitglied im Scope liegt.
3. **Gleiche Korrektur nur, wenn die Allowlist-Bedingung für jede Schwester einzeln erfüllt ist** (z. B. identisches Livery-Artefakt). **Nicht** Werte von einer Variante auf eine andere **blind kopieren**, wenn sich die Ausprägung unterscheidet (z. B. **Wechselstrom vs. Gleichstrom**, andere Epoche): nur anpassen, wenn dieselbe Regel dort **eindeutig** zutrifft.
4. **Ohne dokumentierte Regel** keine automatische Scope-Erweiterung; stattdessen **Pass 1**-Finding («vermutlich Schwester von …, Regel fehlt»).

**Beispiel (nur falls im Repo weiterhin zutreffend):** Roco-Neuheiten mit siebenstelliger Nummer `73` + eine Variantenziffer + gemeinsamer vierstelliger Kern: Schwesterdateien `articles/roco/73{d}{kern}.json` mit `d ∈ {0,1,2}`. Bedeutung der Ziffer `d` und Stromsystem aus Hersteller-/Shop-Konvention ableiten, nicht global raten.

Protokoll: Schwester-Korrekturen explizit markieren (z. B. «Schwester-Variante, gleiche Gruppe wie `articles/<hersteller>/<kern>.json`»).

### Allowlist: Splitting (`model.type` / `model.number`)

Nur **bekannte, im Projekt oder in** [internal/field-parsing-model.md](internal/field-parsing-model.md) **dokumentierte Muster**, wenn **alle** zutreffen:

- Vollständige Betriebsnummer steht **nur** in `model.type` (z. B. Dampf-Präfix «39 1052-8», «38 2566-8»), `model.number` ist `null`, und Baureihe plus Rest sind **eindeutig** splittbar. **Beleg:** mindestens **eine** eindeutige Quelle unter `description` (sachliche erste Zeile), **`source.url`** (Pfadsegment / Slug, z. B. Roco `…-dampflokomotive-38-3713-…`) oder URL erster Zeile **ohne** Widerspruch zwischen diesen Quellen. **OCR in der Beschreibung allein** blockiert den Auto-Fix **nicht**, wenn der **URL-Slug** dieselbe Nummernaufteilung trägt.
- **Dampflok, zweistellig + vier Ziffern (ohne Prüfziffer im Titel):** `model.type` exakt im Muster **`^\d{2} \d{4}$`** (Leerzeichen genau eines), `model.number` ist `null`, `categories` enthält **`dampflokomotive`**, und `source.url` enthält die gleiche Paarung als **`{Baureihe}-{Viererblock}`** (z. B. `38-3713`, `50-1751`) → `model.type` = zweistellige Baureihe, `model.number` = Viererblock. (Häufiger Shop-/Parserrest; siehe Tabelle in `field-parsing-model.md`.)

**Nicht** Auto-Fix: **`model.electricSystem`** (nie aus Marketing-/Fliesstext, Artikelnummer-Heuristik oder Schwesterdatei ableiten; Shops nutzen oft **dieselbe** Beschreibungsbaustelle für mehrere Varianten → **Pass 1**-Finding oder **explizite** User-Anweisung pro Datei). Ausserdem: jede neue Baureihe raten, SNCF/PKP-Mischfälle, **Triebzug- und Set-Artikel** ohne eindeutige Einzel-Lok-Nummer (langer `model.type`, `model.number` null, keine splittbare Betriebsnummer in URL erster Zeile), **kein** konsistenter Nummernbeleg in `description` **und** kein passender Slug in `source.url`. Diese Fälle in **Pass 1** als Finding («Set/Serie, Schwester ggf. prüfen»), nicht raten.

### Allowlist: `model.livery`

Nur **offensichtliche Import-Artefakte** bereinigen:

- Platzhalter wie **«Info: ~»**, **«a a»**, Fragmente wie **«= Li: Oo»** → auf **`null`** setzen (oder ein Wort aus der ersten sauberen Kurzzeile der `description`, wenn dort **ein** eindeutiger Lack-/Zustandsname steht und nichts anderes passt).
- `livery` beginnt mit **Ziffer oder «4»** plus abgeschnittener deutscher Marketingphrase («4Ausführung …», «4Variante …») → **`null`** oder **eine** kurze, aus dem vollen Satz eindeutig ableitbare Bezeichnung (max. ein kurzer Begriff); wenn nicht eindeutig → **kein** Schreiben, Finding in Pass 1.
- Lange **OCR-/Fliesssätze** in `livery` (mehr als ca. 40 Zeichen oder Satzzeichen wie «—» mitten im «Lack») → auf **`null`** kürzen, **nicht** durch erfundenen Marketingtext ersetzen.

### Allowlist: `model.era`

Nur wenn **eindeutig** aus `description` (erste sachliche Zeile) oder URL und **ohne** Widerspruch zu bestehendem `model.era`:

- `model.era` ist **`null`** oder offensichtlicher Tippfehler gegenüber der ersten Beschreibungszeile (z. B. «Epoche VI» vs. `null`) → auf den **kanonischen** Epochen-String aus dem Schema setzen (Projektkonvention: römische Ziffern, Kombinationen wie «III-IV» wie im Datensatz üblich).

Kein Auto-Fix, wenn Epoche im Fliesstext widersprüchlich oder nur im Marketingkörper genannt.

### Allowlist: `model.country` (sehr konservativ)

**Nur** wenn die Zuordnung **praktisch alternativlos** ist:

- `country` **`null`** und `operator` **«K.P.E.V.»** oder gleichwertig klar **Deutsches Kaiserreich** (historisch) → **`DE`**.
- `country` **`null`** und `operator` **«Südbahn»** (k. k. Südbahn) mit AT-Kontext in `description`/`categories` → **`AT`**.

**Nicht** Auto-Fix: **`operator: "DR"`** (DDR vs. DB vs. Lack «DR»), Grenzverkehr, Vermietung (MRCE, Railpool, …), SNCB/SŽ-Mischungen, alles was eine Epochen- oder Staatsgrenze braucht. Dort **Findings**, kein Land raten.

### Nach Auto-Fix

- In **Pass 1** bei betroffenen Dateien kurz vermerken: «Auto-Fix: …» (Felder), damit Phase 2 nicht dieselben Punkte erneut als offen führt, ausser der User wünscht Rücknahme.

## Phasen-Workflow (Pflicht)

### Phase 1: Erstpass über alles

- **Jede** Datei im Scope mindestens kurz anfassen (kein Überspringen im Stillen).
- Ausgabe **ein** zusammenhängendes Dokument **„Pass 1“** mit:
  - Liste aller Dateien (oder Gruppierung nur, wenn der User vorher explizit Gruppierung gleicher Muster wünscht, sonst lieber pro Datei eine Zeile Minimum).
  - Pro Datei: **klar ok** (ein Kurzsatz) **oder** **Findings** (nummeriert pro Datei: `F1`, `F2`, …) und alles **Unklare** (Parsing-Zweifel, Widersprüche, fehlende Felder).
- Keine Rückfrage an den User in Phase 1, ausser Scope unklar.
- Ende Phase 1: kurze **Statistik** (Anzahl Dateien, Anzahl mit Findings/Unklarem, häufige Muster).

### Phase 2: Datei für Datei

- **Genau eine JSON-Datei** pro Agent-Turn bearbeiten (Rückfrage-Runde).
- Nur die **Unklarheiten und Findings** dieser Datei aus Pass 1 vorlegen (mit IDs `F1`, `F2`, …).
- **Eine** klare Frage: was soll mit welchem Punkt passieren (z. B. Split A wählen, Text später anpassen, ignorieren)?
- User-Antworten in dieser Phase:
  - **`skip`:** keine weiteren Entscheidungen zu **dieser** Datei in Phase 2; sofort **nächste** Datei mit offenen Punkten wählen. Offene Punkte dieser Datei in die **Schlussliste** als „skipped (User)“ übernehmen.
  - **`ignore`:** der User bezieht sich auf ein genanntes **Finding** (`ignore F2`) oder auf **alle** offenen Punkte dieser Datei (`ignore all`). Diese Punkte gelten für **diesen Review-Durchlauf** als **ignoriert** (nicht nacharbeiten, nicht nochmals fragen in Phase 2). In der **Schlussliste** als „ignored (this pass)“ führen.
  - Konkrete Anweisung (z. B. „Split A“, „country AT setzen“): Agent notiert als **entschieden** in der laufenden Findings-Liste. **Schreiben** in die JSON nur, wenn der User danach explizit editieren lässt oder Auto-Fix/Änderungslauf dafür schon beauftragt ist.
- Nach jeder User-Antwort: entweder nächstes Finding derselben Datei fragen oder nächste Datei, bis keine Datei mehr mit **nicht** `skip`/`ignore` behandelten offenen Punkten übrig ist (oder User Session beendet).

### Datei in der Antwort (Pflicht, Phase 2)

- Sobald eine **konkrete** `articles/**/*.json` in Phase 2 **im Fokus** steht: in **derselben** Antwort **immer** den **vollen Repo-relativen Pfad** nennen (eine Zeile, z. B. `articles/roco/70078.json` oder `articles/<hersteller>/….json`). **Kein** vollständiger Dateiinhalt in der Antwort, ausser der User verlangt ausdrücklich den Inhalt oder einen Ausschnitt.
- Pass 1: keine Pflicht, alle Pfade einzeln aufzuzählen; bei Phase 2 pro Fokusdatei der Pfad reicht.

### Ignorierte und erneuter Review

- Findings oder Dateien, die in Phase 2 als **`ignore`** markiert wurden, **nicht** von alleine in einem späteren Turn derselben Session wieder aufrollen.
- **Erneutes** Prüfen zuvor ignorierten Inhalts nur, wenn der User **explizit** verlangt (z. B. „zweiter Pass, diesmal inklusive ignorierte“ oder namentlich Dateien nennen).

## Domain-Wissen (progressive disclosure)

| Thema | Datei |
|--------|--------|
| Splitting `model.type` / `model.number` | [internal/field-parsing-model.md](internal/field-parsing-model.md) |
| Baureihen-/UIC-Schemata (Link-Index) | [internal/wiki-baureihen-schemata-uebersicht.md](internal/wiki-baureihen-schemata-uebersicht.md) |
| EVN / 12 Stellen | [internal/wiki-eindeutige-fahrzeugnummer.md](internal/wiki-eindeutige-fahrzeugnummer.md) |
| UIC-Wagennummer, Luhn | [internal/wiki-uic-wagennummer.md](internal/wiki-uic-wagennummer.md) |
| CH Bauartbezeichnungen | [internal/wiki-schweizer-bauartbezeichnungen.md](internal/wiki-schweizer-bauartbezeichnungen.md) |
| ÖBB Überblick | [internal/wiki-oebb-loks-liste.md](internal/wiki-oebb-loks-liste.md) |
| DB Baureihen | [internal/wiki-db-baureihen-liste.md](internal/wiki-db-baureihen-liste.md) |
| DR 1920–1945 (Reichsbahn) | [internal/wiki-dr-reichsbahn-1920-1945-baureihen-liste.md](internal/wiki-dr-reichsbahn-1920-1945-baureihen-liste.md) |
| DDR: DR-Baureihen (1945–1993) | [internal/wiki-dr-ddr-baureihen-liste.md](internal/wiki-dr-ddr-baureihen-liste.md) |
| SNCF Überblick (Frankreich) | [internal/wiki-sncf-loks-liste.md](internal/wiki-sncf-loks-liste.md) |
| Italien Überblick | [internal/wiki-italien-loks-liste.md](internal/wiki-italien-loks-liste.md) |
| Niederlande Überblick | [internal/wiki-niederlande-loks-liste.md](internal/wiki-niederlande-loks-liste.md) |
| Ungarn | [internal/wiki-ungarn-loks-liste.md](internal/wiki-ungarn-loks-liste.md) |
| Rumänien | [internal/wiki-rumaenien-loks-liste.md](internal/wiki-rumaenien-loks-liste.md) |
| Slowenien (nur Dampf) | [internal/wiki-slowenien-dampf-loks-liste.md](internal/wiki-slowenien-dampf-loks-liste.md) |
| Slowakei (ŽSSK) | [internal/wiki-slowakei-zssk-loks-liste.md](internal/wiki-slowakei-zssk-loks-liste.md) |
| Tschechien / ČD / ČSD (Lokklassen; ggf. Bezug SI) | [internal/wiki-tschechien-lokklassen-liste.md](internal/wiki-tschechien-lokklassen-liste.md) |
| Polen PKP | [internal/wiki-polen-pkp-loks-liste.md](internal/wiki-polen-pkp-loks-liste.md) |
| Schweden | [internal/wiki-schweden-loks-kategorien.md](internal/wiki-schweden-loks-kategorien.md) |
| Norwegen | [internal/wiki-norwegen-loks-kategorien.md](internal/wiki-norwegen-loks-kategorien.md) |
| Dänemark DSB | [internal/wiki-daenemark-dsb-loks-liste.md](internal/wiki-daenemark-dsb-loks-liste.md) |
| Luxemburg | [internal/wiki-luxemburg-loks-kategorien.md](internal/wiki-luxemburg-loks-kategorien.md) |
| Belgien (NMBS/SNCB) | [internal/wiki-belgien-nmbs-loks-liste.md](internal/wiki-belgien-nmbs-loks-liste.md) |
| Ordner / Erweiterung | [internal/README.md](internal/README.md) |
| EVN vs Wagen | [reference-evn-uic.md](reference-evn-uic.md) |
| Locobox-Felder | [reference-triebfahrzeug-formate.md](reference-triebfahrzeug-formate.md) |

Vor dem Review: `contracts/article.schema.json` kurz ansehen.

**`internal/wiki-*.md`:** Inhalt ist **komprimiertes Validierungswissen** (Länder, Operatoren, Stromsysteme, typische Baureihen, Kategoriechecks). **Ausnahme:** [wiki-baureihen-schemata-uebersicht.md](internal/wiki-baureihen-schemata-uebersicht.md) ist absichtlich ein **Link-Index**; einige Länderdateien haben ausserdem **einen** Primärlink unter dem Titel (deutsche Wikipedia als Korrektur). Sonst: keine langen Linklisten im Fliesstext; Herkunft weiterhin unter **«Provenienz»** je Datei.

## Inhalt pro Datei (Pass 1 und als Referenz in Phase 2)

Pro Datei mindestens:

- **Roh:** `model.type`, `model.number`, **`model.livery`**, `model.electricSystem`, `model.scale`, `model.era`, `categories` (wenn für den Fehler relevant)
- **Parsing / Split:** sicher / wahrscheinlich / unklar, ggf. Vorschlag A/B
- **Plausibilität:** ok / unklar / widersprüchlich, Stichpunkte (inkl. **Livery vs Sondername** aus Roh-`type` oder Beschreibung; **Stromsystem** vs. Text und vs. **Schwester-Variante** derselben dokumentierten Modellfamilie; **Kategorie** vs. Antrieb; **Triebzug/Set** mit `number` null und langem `type` ohne EVN-Split; **`description`** / **`source.url`** bei OCR-Müll oder deutschsprachigem Fliesstext vs. ausländischem Vorbild)
- **Findings** mit IDs `F1`, `F2`, … für Phase 2

## Schlussliste (Ende Phase 2 oder bei Abbruch)

Ein Abschnitt **„Findings-Übersicht“**:

- **Auto-Fix** (falls gelaufen): kurze Liste `Pfad` + geänderte Felder (kann mit «Erledigt» überlappen).
- **Erledigt / entschieden** (kurz, mit Dateipfad und Finding-ID).
- **Offen** (skipped ohne Resolution).
- **Ignored (this pass)** (Pfad + ID oder „whole file“).

Sprache: Deutsch, **Schweizer Rechtschreibung** (Umlaute, kein Eszett).
