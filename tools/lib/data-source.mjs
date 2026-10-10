import fg from "fast-glob";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { slugifyForUrl } from "../../shared/text-utils.mjs";

const PRIMARY_ARTICLE_GLOB = "data/public-database/articles/**/*.json";
const STANDALONE_ARTICLE_GLOB = "articles/**/*.json";
const FALLBACK_ARTICLE_GLOB = "templates/public-data/articles/**/*.json";
const PRIMARY_MANUFACTURER_GLOB = "data/public-database/config/manufacturers/**/*.json";
const STANDALONE_MANUFACTURER_GLOB = "config/manufacturers/**/*.json";
const FALLBACK_MANUFACTURER_GLOB = "templates/public-data/config/manufacturers/**/*.json";
const TAXONOMY_COLLECTION_GLOBS = {
  categories: {
    primary: "data/public-database/config/categories/**/*.json",
    standalone: "config/categories/**/*.json",
    fallback: "templates/public-data/config/categories/**/*.json"
  },
  tags: {
    primary: "data/public-database/config/tags/**/*.json",
    standalone: "config/tags/**/*.json",
    fallback: "templates/public-data/config/tags/**/*.json"
  },
  scales: {
    primary: "data/public-database/config/scales/**/*.json",
    standalone: "config/scales/**/*.json",
    fallback: "templates/public-data/config/scales/**/*.json"
  },
  electricSystems: {
    primary: "data/public-database/config/electric-systems/**/*.json",
    standalone: "config/electric-systems/**/*.json",
    fallback: "templates/public-data/config/electric-systems/**/*.json"
  },
  decoderInterfaces: {
    primary: "data/public-database/config/decoder-interfaces/**/*.json",
    standalone: "config/decoder-interfaces/**/*.json",
    fallback: "templates/public-data/config/decoder-interfaces/**/*.json"
  },
  features: {
    primary: "data/public-database/config/features/**/*.json",
    standalone: "config/features/**/*.json",
    fallback: "templates/public-data/config/features/**/*.json"
  }
};

async function readJson(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  const raw = await readFile(fullPath, "utf8");
  return JSON.parse(raw);
}

export async function resolveArticlePaths() {
  const primary = await fg(PRIMARY_ARTICLE_GLOB, { dot: false });
  if (primary.length > 0) {
    return primary;
  }
  const standalone = await fg(STANDALONE_ARTICLE_GLOB, { dot: false });
  if (standalone.length > 0) {
    return standalone;
  }
  return fg(FALLBACK_ARTICLE_GLOB, { dot: false });
}

export async function loadArticles() {
  const paths = await resolveArticlePaths();
  const items = [];

  for (const filePath of paths) {
    const article = await readJson(filePath);
    items.push({
      ...article,
      _filePath: filePath,
      manufacturerSlug: slugifyForUrl(article.manufacturer ?? "")
    });
  }

  return items;
}

async function resolveCollectionPaths(collectionKey) {
  const config = TAXONOMY_COLLECTION_GLOBS[collectionKey];
  const primary = await fg(config.primary, { dot: false });
  if (primary.length > 0) {
    return primary;
  }
  const standalone = await fg(config.standalone, { dot: false });
  if (standalone.length > 0) {
    return standalone;
  }
  return fg(config.fallback, { dot: false });
}

export async function loadTaxonomyCollections() {
  const collections = {};
  for (const collectionKey of Object.keys(TAXONOMY_COLLECTION_GLOBS)) {
    const paths = await resolveCollectionPaths(collectionKey);
    collections[collectionKey] = [];
    for (const filePath of paths) {
      const item = await readJson(filePath);
      collections[collectionKey].push({
        ...item,
        _filePath: filePath
      });
    }
  }
  return collections;
}

export async function resolveManufacturerConfigPaths() {
  const primary = await fg(PRIMARY_MANUFACTURER_GLOB, { dot: false });
  if (primary.length > 0) {
    return primary;
  }
  const standalone = await fg(STANDALONE_MANUFACTURER_GLOB, { dot: false });
  if (standalone.length > 0) {
    return standalone;
  }
  return fg(FALLBACK_MANUFACTURER_GLOB, { dot: false });
}

export async function loadManufacturerConfigs() {
  const paths = await resolveManufacturerConfigPaths();
  const items = [];
  for (const filePath of paths) {
    const config = await readJson(filePath);
    items.push({
      ...config,
      _filePath: filePath,
      slug: config.slug ?? slugifyForUrl(config.name ?? "")
    });
  }
  return items;
}
