/**
 * Public data repository has no Astro consumer site. This step keeps the same gate shape as the
 * private platform (`build:site` after `build:index`) by verifying search artifacts exist.
 */
import { access } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const required = [
  path.join(root, "site", "public", "search", "manifest.json"),
  path.join(root, "site", "public", "search", "bulk-records.json")
];

for (const file of required) {
  await access(file);
}

console.log("build:site (public data repo): verified search artifacts after build:index.");
