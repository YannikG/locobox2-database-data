import { mkdir, readdir, unlink, writeFile } from "node:fs/promises";
import { execSync, execFileSync } from "node:child_process";
import path from "node:path";
import {
  loadArticles,
  loadManufacturerConfigs,
  loadTaxonomyCollections
} from "./lib/data-source.mjs";
import { normalizeSearch, slugifyForUrl } from "../shared/text-utils.mjs";
import { normalizeCountryCodeKey } from "./lib/country-flag-key.js";
import { loadCountryFlagSvgForSearchIndex } from "./lib/country-flag-svg-index.mjs";

const ROOT = process.cwd();
const artifactsDir = path.join(ROOT, "artifacts");
const searchDir = path.join(ROOT, "site", "public", "search");

/** Eine Datei für den Worker: ein Fetch, ein JSON.parse statt vieler Shards. */
const SEARCH_BULK_RECORDS_FILE = "bulk-records.json";

/**
 * @param {object} article
 * @param {Map<string, string>} countryFlagSvgByCode
 */
function toSearchRecord(article, countryFlagSvgByCode) {
  const searchBlob = normalizeSearch(
    [
      article.manufacturer,
      article.articleNumber,
      article.model?.operator,
      article.model?.type,
      article.model?.number,
      article.model?.livery,
      article.model?.scale,
      article.model?.electricSystem,
      article.model?.era,
      article.model?.decoderInterface,
      article.model?.couplerSystem,
      ...(article.model?.features ?? [])
    ]
      .filter(Boolean)
      .join(" ")
  );

  const imageUrl =
    typeof article.source?.imageUrl === "string" && article.source.imageUrl.trim().length > 0
      ? article.source.imageUrl.trim()
      : null;

  const countryKey = normalizeCountryCodeKey(article.model?.country);
  const countryFlagSvg = countryKey ? (countryFlagSvgByCode.get(countryKey) ?? "") : "";

  return {
    id: article.id,
    manufacturer: article.manufacturer,
    manufacturerSlug: article.manufacturerSlug,
    articleNumber: article.articleNumber,
    model: article.model,
    imageUrl,
    releaseDate: article.releaseDate ?? null,
    updatedAt: article.updatedAt ?? null,
    lastEditAt: article.lastEdit?.at ?? null,
    searchBlob,
    countryFlagSvg
  };
}

/** @param {object[]} articles */
async function buildCountryFlagSvgByCode(articles) {
  const codes = new Set();
  for (const article of articles) {
    const k = normalizeCountryCodeKey(article.model?.country);
    if (k) {
      codes.add(k);
    }
  }
  const map = new Map();
  await Promise.all(
    [...codes].map(async (code) => {
      map.set(code, await loadCountryFlagSvgForSearchIndex(code));
    })
  );
  return map;
}

/**
 * @param {object[]} articles
 * @param {Map<string, string>} displayNameBySlug aus `config/categories/*.json`
 * @param {Map<string, string>} descriptionBySlug optional, `description` aus denselben Configs
 */
async function buildCategoryArtifacts(articles, displayNameBySlug, descriptionBySlug) {
  const descMap = descriptionBySlug ?? new Map();
  const grouped = new Map();
  for (const article of articles) {
    const rawCategories = Array.isArray(article.categories) ? article.categories : [];
    const seenCategorySlugsForArticle = new Set();
    for (const categoryName of rawCategories) {
      if (typeof categoryName !== "string" || !categoryName.trim()) {
        continue;
      }
      const raw = categoryName.trim();
      const slug = slugifyForUrl(raw);
      if (!slug || seenCategorySlugsForArticle.has(slug)) {
        continue;
      }
      seenCategorySlugsForArticle.add(slug);

      const displayName = displayNameBySlug.get(slug) ?? raw;

      if (!grouped.has(slug)) {
        const fromConfig = descMap.get(slug);
        grouped.set(slug, {
          slug,
          name: displayName,
          description:
            typeof fromConfig === "string" && fromConfig.trim() ? fromConfig.trim() : null,
          articleCount: 0,
          articleIds: []
        });
      }

      const category = grouped.get(slug);
      category.articleCount += 1;
      category.articleIds.push(article.id);
    }
  }

  return [...grouped.values()].sort((a, b) => a.name.localeCompare(b.name, "de"));
}

/** @param {object[]} configs Kategorien- oder Tag-JSON aus `config/**` */
function taxonomyDisplayNameBySlugFromConfigs(configs) {
  const m = new Map();
  for (const c of configs) {
    const slugRaw = typeof c.slug === "string" && c.slug.trim() ? c.slug.trim() : "";
    const slug = slugRaw
      ? slugifyForUrl(slugRaw)
      : slugifyForUrl(typeof c.name === "string" ? c.name : "");
    if (!slug) {
      continue;
    }
    const label = typeof c.name === "string" && c.name.trim() ? c.name.trim() : slugRaw || slug;
    m.set(slug, label);
  }
  return m;
}

/** Kurztext aus `config/categories/*.json` (`description`), gleiche Slug-Logik wie bei Anzeigenamen. */
function taxonomyDescriptionBySlugFromConfigs(configs) {
  const m = new Map();
  for (const c of configs) {
    const slugRaw = typeof c.slug === "string" && c.slug.trim() ? c.slug.trim() : "";
    const slug = slugRaw
      ? slugifyForUrl(slugRaw)
      : slugifyForUrl(typeof c.name === "string" ? c.name : "");
    if (!slug) {
      continue;
    }
    const text =
      typeof c.description === "string" && c.description.trim() ? c.description.trim() : "";
    if (text) {
      m.set(slug, text);
    }
  }
  return m;
}

/**
 * @param {object[]} articles
 * @param {Map<string, string>} displayNameBySlug aus `config/tags/*.json`
 */
async function buildTagArtifacts(articles, displayNameBySlug) {
  const grouped = new Map();
  for (const article of articles) {
    const rawTags = Array.isArray(article.tags) ? article.tags : [];
    const seenTagSlugsForArticle = new Set();
    for (const tagVal of rawTags) {
      if (typeof tagVal !== "string" || !tagVal.trim()) {
        continue;
      }
      const raw = tagVal.trim();
      const slug = slugifyForUrl(raw);
      if (!slug || seenTagSlugsForArticle.has(slug)) {
        continue;
      }
      seenTagSlugsForArticle.add(slug);

      const displayName = displayNameBySlug.get(slug) ?? raw;

      if (!grouped.has(slug)) {
        grouped.set(slug, {
          slug,
          name: displayName,
          articleCount: 0,
          articleIds: []
        });
      }

      const tag = grouped.get(slug);
      tag.articleCount += 1;
      tag.articleIds.push(article.id);
    }
  }

  return [...grouped.values()].sort((a, b) => a.name.localeCompare(b.name, "de"));
}

function resolveLastEditsBatch(sourcePaths) {
  const relevantSourcePaths = sourcePaths.filter(
    (sourcePath) => sourcePath && sourcePath.startsWith("data/public-database/")
  );
  if (relevantSourcePaths.length === 0) {
    return new Map();
  }

  const sourcePathByRepoPath = new Map();
  for (const sourcePath of relevantSourcePaths) {
    const repoPath = sourcePath.replace("data/public-database/", "");
    sourcePathByRepoPath.set(repoPath, sourcePath);
  }

  const metadataBySourcePath = new Map();
  const pendingRepoPaths = new Set(sourcePathByRepoPath.keys());

  try {
    const raw = execFileSync(
      "git",
      [
        "-C",
        "data/public-database",
        "log",
        "--name-only",
        "--format=__COMMIT__%an|%aI|%H",
        "--stdin"
      ],
      {
        input: [...pendingRepoPaths].join("\n"),
        encoding: "utf8",
        stdio: ["pipe", "pipe", "ignore"]
      }
    );

    let currentCommit = null;
    for (const line of raw.split("\n")) {
      if (line.startsWith("__COMMIT__")) {
        const parts = line.replace("__COMMIT__", "").split("|");
        currentCommit =
          parts.length === 3 ? { author: parts[0], at: parts[1], commit: parts[2] } : null;
        continue;
      }

      if (!line || !currentCommit || !pendingRepoPaths.has(line)) {
        continue;
      }

      const sourcePath = sourcePathByRepoPath.get(line);
      if (sourcePath && !metadataBySourcePath.has(sourcePath)) {
        metadataBySourcePath.set(sourcePath, currentCommit);
        pendingRepoPaths.delete(line);
      }
    }
  } catch {
    return new Map();
  }

  return metadataBySourcePath;
}

async function ensureDirs() {
  await mkdir(artifactsDir, { recursive: true });
  await mkdir(searchDir, { recursive: true });
}

/** Frühere `index-*.json`-Shards entfernen, damit nur noch Bulk + Manifest liegen. */
async function removeLegacySearchShardFiles(dir) {
  let names;
  try {
    names = await readdir(dir);
  } catch {
    return;
  }
  await Promise.all(
    names
      .filter((name) => name.startsWith("index-") && name.endsWith(".json"))
      .map((name) => unlink(path.join(dir, name)).catch(() => {}))
  );
}

async function writeJson(filePath, value) {
  await writeFile(filePath, JSON.stringify(value, null, 2) + "\n", "utf8");
}

async function main() {
  await ensureDirs();
  const articles = await loadArticles();
  const manufacturerConfigs = await loadManufacturerConfigs();
  const sourcePaths = articles.map((article) => article._filePath);
  const lastEditBySourcePath = resolveLastEditsBatch(sourcePaths);

  const normalizedArticles = articles.map((article) => {
    const sourcePath = article._filePath;
    return {
      id: article.id,
      manufacturer: article.manufacturer,
      manufacturerSlug: article.manufacturerSlug,
      articleNumber: article.articleNumber,
      setNumber: article.setNumber ?? null,
      releaseDate: article.releaseDate,
      updatedAt: article.updatedAt ?? null,
      uvp: article.uvp,
      model: article.model,
      description: article.description ?? "",
      categories: article.categories ?? [],
      tags: article.tags ?? [],
      source: article.source ?? null,
      sourcePath,
      lastEdit: lastEditBySourcePath.get(sourcePath) ?? null
    };
  });

  await writeJson(path.join(artifactsDir, "articles.json"), normalizedArticles);
  await writeJson(path.join(artifactsDir, "manufacturers.json"), manufacturerConfigs);
  const taxonomy = await loadTaxonomyCollections();
  const categoryDisplayBySlug = taxonomyDisplayNameBySlugFromConfigs(taxonomy.categories ?? []);
  const categoryDescriptionBySlug = taxonomyDescriptionBySlugFromConfigs(taxonomy.categories ?? []);
  const tagDisplayBySlug = taxonomyDisplayNameBySlugFromConfigs(taxonomy.tags ?? []);
  await writeJson(
    path.join(artifactsDir, "categories.json"),
    await buildCategoryArtifacts(
      normalizedArticles,
      categoryDisplayBySlug,
      categoryDescriptionBySlug
    )
  );
  await writeJson(
    path.join(artifactsDir, "tags.json"),
    await buildTagArtifacts(normalizedArticles, tagDisplayBySlug)
  );

  const countryFlagSvgByCode = await buildCountryFlagSvgByCode(normalizedArticles);

  await removeLegacySearchShardFiles(searchDir);

  const bulkRecords = normalizedArticles.map((article) =>
    toSearchRecord(article, countryFlagSvgByCode)
  );
  await writeJson(path.join(searchDir, SEARCH_BULK_RECORDS_FILE), bulkRecords);

  let dataRef = {
    tag: process.env.DATA_TAG ?? null,
    commit: null
  };

  try {
    dataRef.commit = execSync("git -C data/public-database rev-parse HEAD", {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    }).trim();
  } catch {
    try {
      dataRef.commit = execSync("git rev-parse HEAD", {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"]
      }).trim();
    } catch {
      dataRef.commit = null;
    }
  }

  const manifest = {
    generatedAt: new Date().toISOString(),
    recordCount: normalizedArticles.length,
    bulkFile: SEARCH_BULK_RECORDS_FILE,
    shardCount: 0,
    shards: [],
    dataRef
  };

  await writeJson(path.join(searchDir, "manifest.json"), manifest);
  console.log(`Built search index with ${normalizedArticles.length} article(s).`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
