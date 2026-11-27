// Report: model.type-Varianten gruppiert nach Baureihe (Präfix + Leerzeichen ignoriert).
// Usage: node tools/model-type-report.mjs [--json] [--groups-only]
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const ARTICLES = path.join(ROOT, "articles");
const asJson = process.argv.includes("--json");
const groupsOnly = process.argv.includes("--groups-only");

async function walk(dir) {
  const out = [];
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...(await walk(p)));
    else if (e.name.endsWith(".json")) out.push(p);
  }
  return out;
}

export function groupKey(type) {
  return type
    .replace(/[„“"«»]/g, "")
    .replace(/^(?:(?:BR|Rh|Re|Ae|Class|Baureihe|Reihe)\s+)+/i, "")
    .replace(/\s+/g, "")
    .toLowerCase();
}

const files = await walk(ARTICLES);
const rows = [];
for (const f of files) {
  const a = JSON.parse(await readFile(f, "utf8"));
  rows.push({
    file: path.relative(ROOT, f),
    manufacturer: a.manufacturer ?? "",
    type: a.model?.type ?? null,
    operator: a.model?.operator ?? null,
    country: a.model?.country ?? null
  });
}

const counts = new Map();
for (const r of rows) {
  const t = r.type ?? "<null>";
  counts.set(t, (counts.get(t) ?? 0) + 1);
}

const groups = new Map();
for (const [t, n] of counts) {
  if (t === "<null>") continue;
  const k = groupKey(t);
  if (!groups.has(k)) groups.set(k, []);
  groups.get(k).push({ type: t, count: n });
}

const prefixOf = (t) =>
  (t.match(/^(BR|Rh|Re|Ae|Reihe|Baureihe|Class)\s/i)?.[1] ?? "(kein)").toLowerCase();
const multi = [...groups.entries()]
  .filter(([, v]) => v.length > 1)
  .map(([key, variants]) => {
    const groupRows = rows.filter((r) => r.type && groupKey(r.type) === key);
    const countries = [...new Set(groupRows.map((r) => r.country ?? "?"))].sort();
    const prefixes = [...new Set(variants.map((v) => prefixOf(v.type)))].sort();
    return {
      key,
      articles: variants.reduce((s, v) => s + v.count, 0),
      countries,
      prefixMix: prefixes.length > 1,
      prefixes,
      variants: variants.sort((a, b) => b.count - a.count)
    };
  })
  .sort((a, b) => b.articles - a.articles);

const noise = [...counts.entries()]
  .filter(([t]) => t !== "<null>" && (/[„“"«»]/.test(t) || /^\d+$/.test(t.trim())))
  .map(([type, count]) => ({ type, count }))
  .sort((a, b) => b.count - a.count);

const nullCount = counts.get("<null>") ?? 0;

if (asJson) {
  console.log(
    JSON.stringify(
      { total: rows.length, distinctTypes: counts.size, nullCount, multi, noise },
      null,
      2
    )
  );
} else {
  console.log(
    `Artikel: ${rows.length} | distinkte model.type: ${counts.size} | null: ${nullCount}`
  );
  console.log(`Gruppen mit >1 Schreibweise: ${multi.length}`);
  for (const g of multi) {
    console.log(
      `\n[${g.key}] ${g.articles} Artikel | Länder: ${g.countries.join(",")}${g.prefixMix ? " | PRÄFIX-MIX: Land prüfen" : ""}`
    );
    for (const v of g.variants) {
      const who = [
        ...new Set(
          rows
            .filter((r) => r.type === v.type)
            .map((r) => `${r.manufacturer}/${r.country ?? "?"}/${r.operator ?? "?"}`)
        )
      ]
        .slice(0, 3)
        .join(", ");
      console.log(`  ${v.count.toString().padStart(4)}  ${JSON.stringify(v.type)}   ${who}`);
    }
  }
  if (!groupsOnly) {
    console.log(`\nRauschen (Anführungszeichen oder nur Ziffern): ${noise.length}`);
    for (const n of noise)
      console.log(`  ${n.count.toString().padStart(4)}  ${JSON.stringify(n.type)}`);
  }
}
