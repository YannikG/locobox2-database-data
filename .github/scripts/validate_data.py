#!/usr/bin/env python3
"""Validate article and config JSON against contracts and repository conventions."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
ARTICLE_DIR = ROOT / "articles"
CONFIG_DIR = ROOT / "config"

CONFIG_SKIP_NAMES = {"skills-lock.json"}

ARTICLE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def slugify(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value).lower())
    text = re.sub(r"[^\w\s-]", "", text, flags=re.ASCII)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path, errors: list[str]) -> Any | None:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail(errors, f"Invalid JSON in {path.as_posix()}: {exc}")
        return None
    except OSError as exc:
        fail(errors, f"Cannot read {path.as_posix()}: {exc}")
        return None


def load_schema(path: Path, errors: list[str]) -> dict[str, Any] | None:
    data = load_json(path, errors)
    if data is None or not isinstance(data, dict):
        fail(errors, f"Schema must be a JSON object: {path.as_posix()}")
        return None
    return data


def iter_validator_errors(validator: Draft202012Validator, instance: Any, rel: str) -> list[str]:
    out: list[str] = []
    for err in validator.iter_errors(instance):
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        out.append(f"{rel}: schema: {path}: {err.message}")
    return out


def collect_slugs_from_tree(subdir: str, errors: list[str]) -> set[str]:
    slugs: set[str] = set()
    base = CONFIG_DIR / subdir
    if not base.is_dir():
        return slugs
    for path in sorted(base.glob("*.json")):
        data = load_json(path, errors)
        if not isinstance(data, dict):
            continue
        slug = data.get("slug")
        if isinstance(slug, str) and slug.strip():
            slugs.add(slug)
    return slugs


def validate_config_files(errors: list[str], validators: dict[str, Draft202012Validator]) -> None:
    if not CONFIG_DIR.is_dir():
        fail(errors, "Missing config directory")
        return

    duplicate_slugs: dict[str, set[str]] = defaultdict(set)

    for path in sorted(CONFIG_DIR.rglob("*.json")):
        if path.name in CONFIG_SKIP_NAMES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        rel_cfg = path.relative_to(CONFIG_DIR)
        parts = rel_cfg.parts
        if not parts:
            continue

        top = parts[0]
        if top == "manufacturers":
            validator = validators["manufacturer"]
        else:
            validator = validators["taxonomy"]

        data = load_json(path, errors)
        if not isinstance(data, dict):
            fail(errors, f"Config item must be a JSON object in {rel}")
            continue

        errors.extend(iter_validator_errors(validator, data, rel))

        slug = data.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            continue

        if path.stem != slug.lower():
            fail(
                errors,
                f"Config file name must equal slug.lower() ({slug.lower()!r}): {rel}",
            )

        collection = top
        if slug in duplicate_slugs[collection]:
            fail(errors, f"Duplicate slug {slug!r} in config collection {collection!r}: {rel}")
        duplicate_slugs[collection].add(slug)


def validate_articles(
    errors: list[str],
    article_validator: Draft202012Validator,
    slug_sets: dict[str, set[str]],
) -> None:
    if not ARTICLE_DIR.is_dir():
        fail(errors, "Missing articles directory")
        return

    seen_ids: set[str] = set()
    article_keys: set[tuple[str, str]] = set()

    manufacturer_files = {p.stem for p in (CONFIG_DIR / "manufacturers").glob("*.json")} if (
        CONFIG_DIR / "manufacturers"
    ).is_dir() else set()

    for path in sorted(ARTICLE_DIR.rglob("*.json")):
        rel = path.relative_to(ROOT).as_posix()
        data = load_json(path, errors)
        if not isinstance(data, dict):
            fail(errors, f"Article must be a JSON object in {rel}")
            continue

        errors.extend(iter_validator_errors(article_validator, data, rel))

        rel_parts = path.relative_to(ARTICLE_DIR).parts
        if len(rel_parts) != 2:
            fail(errors, f"Article path must be articles/<manufacturer>/<articleNumber>.json: {rel}")
            continue

        manufacturer_slug_from_path = rel_parts[0]
        article_number_from_path = path.stem

        manufacturer = data.get("manufacturer")
        if not isinstance(manufacturer, str) or not manufacturer.strip():
            fail(errors, f"Field manufacturer must be a non-empty string in {rel}")
            expected_slug = ""
        else:
            expected_slug = slugify(manufacturer)

        if expected_slug and manufacturer_slug_from_path != expected_slug:
            fail(
                errors,
                f"Manufacturer folder must match slugified manufacturer ({expected_slug!r}): {rel}",
            )

        article_number = data.get("articleNumber")
        if not isinstance(article_number, str) or article_number != article_number_from_path:
            fail(errors, f"articleNumber must match filename in {rel}")

        article_id = data.get("id")
        if not isinstance(article_id, str) or not ARTICLE_ID_RE.fullmatch(article_id):
            fail(errors, f"Invalid article id in {rel}")
        elif expected_slug and article_number and article_id != f"{expected_slug}-{article_number}":
            fail(
                errors,
                f"Article id must be {expected_slug!r}-{article_number!r} in {rel}",
            )

        if isinstance(article_id, str) and ARTICLE_ID_RE.fullmatch(article_id):
            if article_id in seen_ids:
                fail(errors, f"Duplicate article id {article_id!r} in {rel}")
            seen_ids.add(article_id)

        if expected_slug and isinstance(article_number, str):
            key = (expected_slug, article_number)
            if key in article_keys:
                fail(errors, f"Duplicate manufacturer/articleNumber in {rel}")
            article_keys.add(key)

        if expected_slug and expected_slug not in manufacturer_files:
            fail(
                errors,
                f"Unknown manufacturer slug {expected_slug!r} (missing config/manufacturers/"
                f"{expected_slug}.json): {rel}",
            )

        for cat in data.get("categories") or []:
            if not isinstance(cat, str):
                fail(errors, f"categories entries must be strings in {rel}")
                continue
            if cat not in slug_sets["categories"]:
                fail(errors, f"Unknown category slug {cat!r} in {rel}")

        for tag in data.get("tags") or []:
            if not isinstance(tag, str):
                fail(errors, f"tags entries must be strings in {rel}")
                continue
            if tag not in slug_sets["tags"]:
                fail(errors, f"Unknown tag slug {tag!r} in {rel}")

        model = data.get("model")
        if isinstance(model, dict):
            scale = model.get("scale")
            if isinstance(scale, str) and scale and scale not in slug_sets["scales"]:
                fail(errors, f"Unknown model.scale slug {scale!r} in {rel}")
            es = model.get("electricSystem")
            if isinstance(es, str) and es and es not in slug_sets["electric-systems"]:
                fail(errors, f"Unknown model.electricSystem slug {es!r} in {rel}")


def main() -> int:
    errors: list[str] = []

    article_schema = load_schema(CONTRACTS / "article.schema.json", errors)
    taxonomy_schema = load_schema(CONTRACTS / "taxonomy-item.schema.json", errors)
    manufacturer_schema = load_schema(CONTRACTS / "manufacturer.schema.json", errors)
    if article_schema is None or taxonomy_schema is None or manufacturer_schema is None:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    fc = Draft202012Validator.FORMAT_CHECKER
    article_validator = Draft202012Validator(article_schema, format_checker=fc)
    taxonomy_validator = Draft202012Validator(taxonomy_schema, format_checker=fc)
    manufacturer_validator = Draft202012Validator(manufacturer_schema, format_checker=fc)

    slug_sets = {
        "categories": collect_slugs_from_tree("categories", errors),
        "tags": collect_slugs_from_tree("tags", errors),
        "scales": collect_slugs_from_tree("scales", errors),
        "electric-systems": collect_slugs_from_tree("electric-systems", errors),
    }

    validate_config_files(
        errors,
        {"taxonomy": taxonomy_validator, "manufacturer": manufacturer_validator},
    )
    validate_articles(errors, article_validator, slug_sets)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"\nValidation failed with {len(errors)} error(s).")
        return 1

    print("Validation successful.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
