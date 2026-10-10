import { readFile } from "node:fs/promises";
import path from "node:path";

export const ALLOWED_SOURCE_HOSTS_REL = "config/allowed-source-hosts.json";

const HOST_RE = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$/;

/**
 * @param {unknown} data
 * @returns {{ hosts: Set<string> }}
 */
export function parseAllowedSourceHosts(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error(`${ALLOWED_SOURCE_HOSTS_REL}: root must be a JSON object`);
  }
  const hostsRaw = data.hosts;
  if (!Array.isArray(hostsRaw) || hostsRaw.length === 0) {
    throw new Error(`${ALLOWED_SOURCE_HOSTS_REL}: hosts must be a non-empty array`);
  }
  const hosts = new Set();
  for (const entry of hostsRaw) {
    if (typeof entry !== "string" || !entry.trim()) {
      throw new Error(`${ALLOWED_SOURCE_HOSTS_REL}: hosts entries must be non-empty strings`);
    }
    const host = entry.trim().toLowerCase();
    if (!HOST_RE.test(host)) {
      throw new Error(`${ALLOWED_SOURCE_HOSTS_REL}: invalid hostname ${JSON.stringify(entry)}`);
    }
    if (hosts.has(host)) {
      throw new Error(`${ALLOWED_SOURCE_HOSTS_REL}: duplicate hostname ${host}`);
    }
    hosts.add(host);
  }
  return { hosts };
}

/**
 * @param {string} sourceUrl
 * @param {Set<string>} allowedHosts
 * @returns {{ ok: true, host: string } | { ok: false, reason: string }}
 */
export function checkSourceUrlHost(sourceUrl, allowedHosts) {
  let parsed;
  try {
    parsed = new URL(sourceUrl);
  } catch {
    return { ok: false, reason: `invalid URL ${sourceUrl}` };
  }
  if (parsed.protocol !== "https:") {
    return { ok: false, reason: `source must use https: (${sourceUrl})` };
  }
  const host = parsed.hostname.toLowerCase();
  if (!allowedHosts.has(host)) {
    return {
      ok: false,
      reason: `host ${host} is not in ${ALLOWED_SOURCE_HOSTS_REL} (${sourceUrl})`
    };
  }
  return { ok: true, host };
}

/**
 * @param {string} [cwd]
 * @returns {Promise<{ hosts: Set<string> }>}
 */
export async function loadAllowedSourceHosts(cwd = process.cwd()) {
  const filePath = path.join(cwd, ALLOWED_SOURCE_HOSTS_REL);
  const raw = await readFile(filePath, "utf8");
  return parseAllowedSourceHosts(JSON.parse(raw));
}
