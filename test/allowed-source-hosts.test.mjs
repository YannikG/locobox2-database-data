import assert from "node:assert/strict";
import test from "node:test";
import { checkSourceUrlHost, parseAllowedSourceHosts } from "../tools/lib/allowed-source-hosts.mjs";

test("parseAllowedSourceHosts accepts unique lowercase hosts", () => {
  const { hosts } = parseAllowedSourceHosts({
    schemaVersion: "1.0.0",
    hosts: ["www.roco.cc", "WWW.PIKO.DE"]
  });
  assert.equal(hosts.has("www.roco.cc"), true);
  assert.equal(hosts.has("www.piko.de"), true);
  assert.equal(hosts.size, 2);
});

test("parseAllowedSourceHosts rejects duplicates and bad hosts", () => {
  assert.throws(() => parseAllowedSourceHosts({ hosts: ["www.roco.cc", "www.roco.cc"] }));
  assert.throws(() => parseAllowedSourceHosts({ hosts: ["not a host"] }));
  assert.throws(() => parseAllowedSourceHosts({ hosts: [] }));
});

test("checkSourceUrlHost enforces https and allowlist", () => {
  const allowed = new Set(["www.roco.cc"]);
  assert.equal(checkSourceUrlHost("https://www.roco.cc/catalog.pdf", allowed).ok, true);
  assert.equal(checkSourceUrlHost("http://www.roco.cc/catalog.pdf", allowed).ok, false);
  assert.equal(checkSourceUrlHost("https://evil.example/x", allowed).ok, false);
});
