import assert from "node:assert/strict";
import test from "node:test";
import { normalizeCountryCodeKey, resolvePackageIso2Code } from "../tools/lib/country-flag-key.js";

test("normalizeCountryCodeKey returns uppercase ISO-2", () => {
  assert.equal(normalizeCountryCodeKey("de"), "DE");
  assert.equal(normalizeCountryCodeKey("  ch  "), "CH");
});

test("normalizeCountryCodeKey strips non-letters then requires length 2", () => {
  assert.equal(normalizeCountryCodeKey("D-E"), "DE");
  assert.equal(normalizeCountryCodeKey("D"), "");
  assert.equal(normalizeCountryCodeKey("DEU"), "");
  assert.equal(normalizeCountryCodeKey(""), "");
  assert.equal(normalizeCountryCodeKey(null), "");
});

test("resolvePackageIso2Code maps CS to CZ for country-flag-icons", () => {
  assert.equal(resolvePackageIso2Code("CS"), "CZ");
  assert.equal(resolvePackageIso2Code("DE"), "DE");
});
