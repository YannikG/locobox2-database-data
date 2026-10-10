from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from locobox_cli.interfaces.cli.main import app

FIXTURE = Path(__file__).parent / "fixtures" / "roco_pdp_sample.html"
REPO = Path(__file__).resolve().parents[3]


def test_shop_parse_continues_after_article_mismatch(tmp_path: Path) -> None:
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    good = FIXTURE.read_text(encoding="utf-8")
    # Wrong stem triggers article mismatch against og:url …/70035-…
    (html_dir / "99999.html").write_text(good, encoding="utf-8")
    (html_dir / "70035.html").write_text(good, encoding="utf-8")

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
            str(REPO),
            "--no-pipeline",
            "--no-write",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["fail"] == 1
    by_art = {r["article"]: r for r in payload["results"]}
    assert by_art["99999"]["ok"] is False
    assert by_art["70035"]["ok"] is True
