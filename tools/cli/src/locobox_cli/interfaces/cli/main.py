from __future__ import annotations

import typer

from locobox_cli.interfaces.cli import (
    articles_cmds,
    catalog_cmds,
    pipeline_cmds,
    queue_cmds,
    shop_cmds,
    tags_cmds,
)

app = typer.Typer(
    name="locobox",
    help="Locobox article import tools (queue, pipeline, shop).",
    no_args_is_help=True,
)
app.add_typer(queue_cmds.app, name="queue")
app.add_typer(pipeline_cmds.app, name="pipeline")
app.add_typer(articles_cmds.app, name="articles")
app.add_typer(catalog_cmds.app, name="catalog")
app.add_typer(shop_cmds.app, name="shop")
app.add_typer(tags_cmds.app, name="tags")


@app.callback()
def _root() -> None:
    """Locobox CLI."""


def main() -> None:
    app()


if __name__ == "__main__":
    main()
