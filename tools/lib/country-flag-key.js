/**
 * Normalisiert Roh-Ländercodes auf genau zwei Grossbuchstaben (ISO-3166-1 alpha-2
 * oder historische Codes wie DD, CS), sonst leerer String.
 * @param {unknown} iso2
 * @returns {string}
 */
export function normalizeCountryCodeKey(iso2) {
  const key = String(iso2 ?? "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z]/g, "");
  return key.length === 2 ? key : "";
}

/** Historische Codes → ISO-3166-1 alpha-2 in `country-flag-icons` (gleiche Flagge). */
const PACKAGE_ISO2_BY_HISTORICAL = Object.freeze({
  /** Tschechoslowakei: aktuelle Flagge der Tschechischen Republik. */
  CS: "CZ"
});

/**
 * ISO-2-Code für den Lookup in `country-flag-icons` (Alias für historische Codes).
 * @param {string} canonicalKey Ergebnis von {@link normalizeCountryCodeKey}.
 * @returns {string}
 */
export function resolvePackageIso2Code(canonicalKey) {
  return PACKAGE_ISO2_BY_HISTORICAL[canonicalKey] ?? canonicalKey;
}
