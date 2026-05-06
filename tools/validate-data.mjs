import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { readFile } from "node:fs/promises";
import path from "node:path";
import {
  loadArticles,
  loadManufacturerConfigs,
  loadTaxonomyCollections
} from "./lib/data-source.mjs";
import { slugifyForUrl } from "../shared/text-utils.mjs";

const ROOT = process.cwd();

async function readJson(filePath) {
  const raw = await readFile(path.join(ROOT, filePath), "utf8");
  return JSON.parse(raw);
}

function createAjv() {
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  return ajv;
}

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

function validateSemantics(articles) {
  const ids = new Set();
  for (const article of articles) {
    if (typeof article.manufacturer === "string" && typeof article.articleNumber === "string") {
      const expectedId = `${slugifyForUrl(article.manufacturer)}-${article.articleNumber}`;
      if (article.id !== expectedId) {
        fail(
          `Article id must match manufacturer and article number (${expectedId}) in ${article._filePath}`
        );
      }
    }

    if (ids.has(article.id)) {
      fail(`Duplicate article id: ${article.id}`);
    }
    ids.add(article.id);

    if (!article.description) {
      continue;
    }

    if (typeof article.description !== "string") {
      fail(`Description is invalid in ${article._filePath}`);
    }
  }
}

function validateTaxonomyCollectionIntegrity(taxonomyCollections) {
  for (const [collectionName, items] of Object.entries(taxonomyCollections)) {
    const slugs = new Map();
    const names = new Map();

    for (const item of items) {
      if (typeof item.slug === "string" && item.slug.length > 0) {
        if (slugs.has(item.slug)) {
          fail(
            `Duplicate taxonomy slug "${item.slug}" in collection "${collectionName}" (${slugs.get(item.slug)} and ${item._filePath})`
          );
        } else {
          slugs.set(item.slug, item._filePath);
        }
      }

      if (typeof item.name === "string" && item.name.length > 0) {
        const normalizedName = item.name.toLocaleLowerCase("de-CH");
        if (names.has(normalizedName)) {
          fail(
            `Duplicate taxonomy name "${item.name}" in collection "${collectionName}" (${names.get(normalizedName)} and ${item._filePath})`
          );
        } else {
          names.set(normalizedName, item._filePath);
        }
      }
    }
  }
}

function validateManufacturerReferences(articles, manufacturerConfigs) {
  const manufacturersBySlug = new Set(
    manufacturerConfigs.map((config) => slugifyForUrl(config.slug ?? config.name ?? ""))
  );

  for (const article of articles) {
    if (
      typeof article.manufacturer === "string" &&
      !manufacturersBySlug.has(slugifyForUrl(article.manufacturer))
    ) {
      fail(
        `Manufacturer "${article.manufacturer}" in ${article._filePath} is missing in config/manufacturers`
      );
    }
  }
}

function validateArticlePathConvention(articles) {
  for (const article of articles) {
    const match = article._filePath.match(/articles\/([^/]+)\/([^/]+)\.json$/);
    if (!match) {
      fail(
        `Article path must be articles/{manufacturerSlug}/{articleNumber}.json: ${article._filePath}`
      );
      continue;
    }
    const [, manufacturerSlug, articleNumberFromPath] = match;
    if (manufacturerSlug !== slugifyForUrl(article.manufacturer)) {
      fail(`Manufacturer slug in path does not match article manufacturer: ${article._filePath}`);
    }
    if (articleNumberFromPath !== article.articleNumber) {
      fail(`Article number in path does not match article payload: ${article._filePath}`);
    }
  }
}

function buildAllowedValueSet(items) {
  const values = new Set();
  for (const item of items) {
    values.add(item.name);
    values.add(item.slug);
    for (const alias of item.aliases ?? []) {
      values.add(alias);
    }
  }
  return values;
}

function validateArticleTaxonomyReferences(articles, taxonomyCollections) {
  const allowedCategories = buildAllowedValueSet(taxonomyCollections.categories ?? []);
  const allowedTags = buildAllowedValueSet(taxonomyCollections.tags ?? []);
  const allowedScales = buildAllowedValueSet(taxonomyCollections.scales ?? []);
  const allowedElectricSystems = buildAllowedValueSet(taxonomyCollections.electricSystems ?? []);
  const allowedDecoderInterfaces = buildAllowedValueSet(
    taxonomyCollections.decoderInterfaces ?? []
  );
  const allowedFeatures = buildAllowedValueSet(taxonomyCollections.features ?? []);

  for (const article of articles) {
    for (const category of article.categories ?? []) {
      if (!allowedCategories.has(category)) {
        fail(`Unknown category "${category}" in ${article._filePath}`);
      }
    }
    for (const tag of article.tags ?? []) {
      if (!allowedTags.has(tag)) {
        fail(`Unknown tag "${tag}" in ${article._filePath}`);
      }
    }
    for (const feature of article.model?.features ?? []) {
      if (!allowedFeatures.has(feature)) {
        fail(`Unknown feature "${feature}" in ${article._filePath}`);
      }
    }

    if (!allowedScales.has(article.model.scale)) {
      fail(`Unknown scale "${article.model.scale}" in ${article._filePath}`);
    }
    if (!allowedElectricSystems.has(article.model.electricSystem)) {
      fail(`Unknown electricSystem "${article.model.electricSystem}" in ${article._filePath}`);
    }
    if (
      article.model.decoderInterface &&
      !allowedDecoderInterfaces.has(article.model.decoderInterface)
    ) {
      fail(`Unknown decoderInterface "${article.model.decoderInterface}" in ${article._filePath}`);
    }
  }
}

async function main() {
  const ajv = createAjv();
  const articleSchema = await readJson("contracts/article.schema.json");
  const taxonomyItemSchema = await readJson("contracts/taxonomy-item.schema.json");
  const manufacturerSchema = await readJson("contracts/manufacturer.schema.json");

  const validateArticle = ajv.compile(articleSchema);
  const validateTaxonomyItem = ajv.compile(taxonomyItemSchema);
  const validateManufacturer = ajv.compile(manufacturerSchema);

  const articles = await loadArticles();
  const taxonomyCollections = await loadTaxonomyCollections();
  const manufacturerConfigs = await loadManufacturerConfigs();

  for (const article of articles) {
    const articlePayload = { ...article };
    delete articlePayload._filePath;
    delete articlePayload.manufacturerSlug;
    const valid = validateArticle(articlePayload);
    if (!valid) {
      fail(`Schema validation failed for ${article._filePath}`);
      for (const err of validateArticle.errors ?? []) {
        fail(`  ${err.instancePath} ${err.message}`);
      }
    }
  }

  for (const [collectionName, items] of Object.entries(taxonomyCollections)) {
    for (const item of items) {
      const itemPayload = { ...item };
      delete itemPayload._filePath;
      const valid = validateTaxonomyItem(itemPayload);
      if (!valid) {
        fail(`${collectionName} item validation failed for ${item._filePath}`);
        for (const err of validateTaxonomyItem.errors ?? []) {
          fail(`  ${err.instancePath} ${err.message}`);
        }
      }
    }
  }

  for (const config of manufacturerConfigs) {
    const configPayload = { ...config };
    delete configPayload._filePath;
    const valid = validateManufacturer(configPayload);
    if (!valid) {
      fail(`Manufacturer config validation failed for ${config._filePath}`);
      for (const err of validateManufacturer.errors ?? []) {
        fail(`  ${err.instancePath} ${err.message}`);
      }
    }
  }

  validateSemantics(articles);
  validateArticlePathConvention(articles);
  validateArticleTaxonomyReferences(articles, taxonomyCollections);
  validateTaxonomyCollectionIntegrity(taxonomyCollections);
  validateManufacturerReferences(articles, manufacturerConfigs);

  if (process.exitCode) {
    console.error(
      "\nvalidate-data: validation failed. Search this log above for the first error lines (schema paths, unknown category/tag/feature/scale/electricSystem/decoderInterface, duplicates, path mismatches).\n"
    );
    throw new Error("Validation failed");
  }

  console.log(
    `Validated ${articles.length} article(s), ${manufacturerConfigs.length} manufacturer config(s), and ${Object.values(
      taxonomyCollections
    ).reduce((sum, entries) => sum + entries.length, 0)} taxonomy item file(s) successfully.`
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
