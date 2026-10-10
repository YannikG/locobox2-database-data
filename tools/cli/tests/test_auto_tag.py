from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from locobox_cli.application.tags.taxonomy import TagTaxonomy, normalize_tag_slug
from locobox_cli.interfaces.cli.main import app

REPO = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).parent / "fixtures" / "roco_pdp_sample.html"
SCHEMA = REPO / "contracts" / "article.schema.json"


def _mini_repo(tmp: Path) -> Path:
    (tmp / "contracts").mkdir()
    shutil.copy(SCHEMA, tmp / "contracts" / "article.schema.json")
    (tmp / "config" / "tags").mkdir(parents=True)
    (tmp / "articles" / "roco").mkdir(parents=True)
    (tmp / "rules").mkdir(parents=True)
    return tmp


def _minimal_article(*, tags: list[str] | None = None) -> dict:
    return {
        "schemaVersion": "1.0.0",
        "id": "roco-70035",
        "manufacturer": "Roco",
        "articleNumber": "70035",
        "releaseDate": "2024",
        "uvp": {"amount": 100.0, "currency": "EUR"},
        "model": {
            "country": "DE",
            "operator": "DB",
            "type": "T3",
            "number": None,
            "livery": None,
            "scale": "H0",
            "electricSystem": "DC-Analog",
            "decoderInterface": "Unbekannt",
            "era": "I",
        },
        "description": "Test",
        "categories": ["lokomotive"],
        "tags": tags or [],
        "source": {
            "url": "https://www.roco.cc/rde/produkte/lokomotiven/dampflokomotiven/70035-x.html",
            "notes": "t",
        },
        "updatedAt": "2024-01-01T00:00:00Z",
    }


def test_normalize_tag_slug() -> None:
    assert normalize_tag_slug("Piko_Neuheiten_2020") == "piko-neuheiten-2020"


def test_tags_ensure_creates_and_is_idempotent(tmp_path: Path) -> None:
    root = _mini_repo(tmp_path)
    runner = CliRunner()
    r1 = runner.invoke(
        app,
        ["tags", "ensure", "--slug", "piko-neuheiten-2020", "--repo-root", str(root)],
    )
    assert r1.exit_code == 0, r1.stdout
    p1 = json.loads(r1.stdout)
    assert p1["created"] is True
    assert (root / "config" / "tags" / "piko-neuheiten-2020.json").is_file()
    r2 = runner.invoke(
        app,
        ["tags", "ensure", "--slug", "piko-neuheiten-2020", "--repo-root", str(root)],
    )
    assert r2.exit_code == 0
    assert json.loads(r2.stdout)["created"] is False


def test_shop_parse_skips_existing_json(tmp_path: Path) -> None:
    root = _mini_repo(tmp_path)
    art = root / "articles" / "roco" / "70035.json"
    art.write_text(json.dumps(_minimal_article(), ensure_ascii=False, indent=2) + "\n")
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    (html_dir / "70035.html").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "shop",
            "parse",
            "--source",
            "roco",
            "--html-dir",
            str(html_dir),
            "--repo-root",
            str(root),
            "--no-pipeline",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["skipped"] == 1
    assert payload["results"][0]["action"] == "skipped_existing"
    # body unchanged (still minimal, not shop parse)
    assert json.loads(art.read_text())["description"] == "Test"


def test_shop_parse_append_tag_if_exists(tmp_path: Path) -> None:
    root = _mini_repo(tmp_path)
    TagTaxonomy(root).ensure("roco-neuheiten-2024")
    art = root / "articles" / "roco" / "70035.json"
    art.write_text(json.dumps(_minimal_article(tags=[]), ensure_ascii=False, indent=2) + "\n")
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    (html_dir / "70035.html").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "shop",
            "parse",
            "--source",
            "roco",
            "--html-dir",
            str(html_dir),
            "--repo-root",
            str(root),
            "--tag",
            "roco-neuheiten-2024",
            "--append-tag-if-exists",
            "--no-pipeline",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["appended"] == 1
    data = json.loads(art.read_text())
    assert data["tags"] == ["roco-neuheiten-2024"]
    assert data["description"] == "Test"


def test_shop_parse_unknown_tag_fails(tmp_path: Path) -> None:
    root = _mini_repo(tmp_path)
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    (html_dir / "70035.html").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "shop",
            "parse",
            "--source",
            "roco",
            "--html-dir",
            str(html_dir),
            "--repo-root",
            str(root),
            "--tag",
            "does-not-exist-yet",
            "--no-pipeline",
            "--no-write",
        ],
    )
    assert result.exit_code == 1
    assert "tags ensure" in result.stdout


def test_articles_append_tag_idempotent(tmp_path: Path) -> None:
    root = _mini_repo(tmp_path)
    TagTaxonomy(root).ensure("roco-neuheiten-2024")
    art = root / "articles" / "roco" / "70035.json"
    art.write_text(
        json.dumps(_minimal_article(tags=["roco-neuheiten-2024"]), ensure_ascii=False, indent=2)
        + "\n"
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "articles",
            "append-tag",
            "--mfr",
            "roco",
            "--article",
            "70035",
            "--tag",
            "roco-neuheiten-2024",
            "--repo-root",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["changed"] == 0
    assert payload["results"][0]["skipped"] is True
