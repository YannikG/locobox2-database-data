// Normalisiert model.type-Schreibweisen (Dry-Run standard, --apply schreibt).
// Regeln (konservativ, nur eindeutige Fälle):
//  1. Ganzer Wert in Anführungszeichen („Sik“, "Desiro") → ohne Anführungszeichen.
//  2. "EU43" → "EU 43" (Leerzeichen).
//  3. DE/DD: "193", "BR 193", "E 44" → "BR 193" / "BR E 44", nur wenn es für die Baureihe
//     im Repo bereits eine "BR …"-Schreibweise gibt.
//  4. AT: "1216", "Reihe 1216" → "Rh 1216", nur wenn "Rh 1216" im Repo bereits existiert
//     (Konvention laut internal/wiki-oebb-loks-liste.md: Rh = Reihe). Zusätzlich ÖBB-Operator:
//     "BR 1020" / "Reihe 1020" → "Rh 1020".
// Alles andere (Prefix-Mischungen BR/Re/Rh, Ländergrenzen) bleibt und wird gemeldet.
// Usage: node tools/normalize-model-type.mjs [--apply]
import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const APPLY = process.argv.includes("--apply");

async function walk(dir) {
  const out = [];
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...(await walk(p)));
    else if (e.name.endsWith(".json")) out.push(p);
  }
  return out;
}

export function stripWholeQuotes(t) {
  const m = t.match(/^[„"«]\s*(.+?)\s*[“"»]$/);
  return m ? m[1] : t;
}

export function groupKey(type) {
  return type
    .replace(/[„“"«»]/g, "")
    .replace(/^(?:(?:BR|Rh|Re|Ae|Class|Baureihe|Reihe)\s+)+/i, "")
    .replace(/\s+/g, "")
    .toLowerCase();
}

const files = await walk(path.join(ROOT, "articles"));
const arts = [];
for (const f of files) {
  const raw = await readFile(f, "utf8");
  arts.push({ f, raw, data: JSON.parse(raw) });
}

// Vorhandene Schreibweisen je Gruppe (Präfix-Sets) für Regel 3/4
const hasExact = new Set(arts.map((a) => a.data.model?.type).filter(Boolean));

const changes = [];
for (const a of arts) {
  const m = a.data.model;
  if (!m || typeof m.type !== "string") continue;
  const before = m.type;
  const country = m.country;
  let t = stripWholeQuotes(before.trim());
  t = t.replace(/^EU(\d)/, "EU $1");

  const bare = t.match(/^(?:BR\s+)?(\d[\d.]*)$/);
  const eBare = t.match(/^(?:BR\s+)?E\s?(\d+)$/);
  // dreistellig mit führender Null (038, 086) ist Tippfehler-Verdacht → nicht automatisch
  const leadingZeroTypo = bare && /^0\d{2}$/.test(bare[1]);
  if (
    (country === "DE" || country === "DD") &&
    bare &&
    !leadingZeroTypo &&
    hasExact.has(`BR ${bare[1]}`)
  ) {
    t = `BR ${bare[1]}`;
  } else if ((country === "DE" || country === "DD") && eBare && hasExact.has(`BR E ${eBare[1]}`)) {
    t = `BR E ${eBare[1]}`;
  }

  const at = t.match(/^(?:Rh\s+|Reihe\s+)?(\d[\d.]*)$/);
  if (country === "AT" && at && !/^0\d{2}$/.test(at[1]) && hasExact.has(`Rh ${at[1]}`)) {
    t = `Rh ${at[1]}`;
  }
  // ÖBB: "BR 1020" / "Reihe 2016" → "Rh 2016" (Konvention laut wiki-oebb-loks-liste.md)
  const oebbPrefixed = t.match(/^(?:BR|Reihe)\s+(\d[\d.]*)$/);
  if (country === "AT" && oebbPrefixed && /^ÖBB/.test(m.operator ?? "")) {
    t = `Rh ${oebbPrefixed[1]}`;
  }

  // CH: SBB-Konvention "Re NNN" (Skill: ÖBB/SBB Reihe/Re nicht als Rh). Nur wenn "Re NNN" im Repo existiert.
  const chNum = t.match(/^(?:BR\s+|Reihe\s+|Rh\s+|Re\s+)?(\d{3})$/);
  if (country === "CH" && chNum && !/^0/.test(chNum[1]) && hasExact.has(`Re ${chNum[1]}`)) {
    t = `Re ${chNum[1]}`;
  }

  if (t !== before) changes.push({ file: path.relative(ROOT, a.f), before, after: t, country, a });
}

const byRule = {};
for (const c of changes) {
  const k = `${c.before} → ${c.after}`;
  byRule[k] = (byRule[k] ?? 0) + 1;
}
console.log(`Änderungen: ${changes.length} Artikel`);
for (const [k, n] of Object.entries(byRule).sort((x, y) => y[1] - x[1]))
  console.log(`  ${String(n).padStart(4)}  ${k}`);

// Nur der Wert von model.type wird textuell ersetzt (kein JSON-Neuschreiben,
// damit Zahlen wie 375.0 und alle übrigen Felder unverändert bleiben).
if (APPLY) {
  for (const c of changes) {
    const modelAt = c.a.raw.indexOf('"model": {');
    const key = `"type": ${JSON.stringify(c.before)}`;
    const at = c.a.raw.indexOf(key, modelAt);
    if (modelAt < 0 || at < 0) throw new Error(`model.type nicht gefunden: ${c.file}`);
    const next =
      c.a.raw.slice(0, at) + `"type": ${JSON.stringify(c.after)}` + c.a.raw.slice(at + key.length);
    JSON.parse(next);
    await writeFile(c.a.f, next, "utf8");
  }
  console.log(`geschrieben: ${changes.length}`);
}
