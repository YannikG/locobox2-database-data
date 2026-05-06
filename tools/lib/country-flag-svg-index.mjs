import { readFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { normalizeCountryCodeKey, resolvePackageIso2Code } from "./country-flag-key.js";

function stripXmlDeclaration(svg) {
  return svg.replace(/^<\?xml[^?]*\?>\s*/i, "").trim();
}

async function loadPackageFlagSvg(packageKey) {
  const file = path.join(
    process.cwd(),
    "node_modules",
    "country-flag-icons",
    "string",
    "3x2",
    `${packageKey}.js`
  );
  try {
    const mod = await import(pathToFileURL(file).href);
    return typeof mod.default === "string" ? mod.default : "";
  } catch {
    return "";
  }
}

async function loadLocalFlagSvgFallback(key) {
  try {
    const file = path.join(process.cwd(), "site", "public", "flags", `${key}.svg`);
    const raw = await readFile(file, "utf8");
    return typeof raw === "string" ? stripXmlDeclaration(raw) : "";
  } catch {
    return "";
  }
}

/**
 * Gleiche Logik wie `site/src/lib/country-flag.js`, für Node beim `build:index`
 * (ohne Vite `import.meta.glob`).
 * @param {unknown} iso2
 * @returns {Promise<string>}
 */
export async function loadCountryFlagSvgForSearchIndex(iso2) {
  const key = normalizeCountryCodeKey(iso2);
  if (!key) {
    return "";
  }
  const fromPackage = await loadPackageFlagSvg(resolvePackageIso2Code(key));
  if (fromPackage) {
    return fromPackage;
  }
  return loadLocalFlagSvgFallback(key);
}
