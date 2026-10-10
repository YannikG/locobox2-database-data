from __future__ import annotations

ALLOWED_SET_PATHS: frozenset[str] = frozenset(
    {
        "model.type",
        "model.number",
        "model.livery",
        "model.operator",
        "model.country",
        "model.era",
        "model.scale",
        "model.electricSystem",
        "model.decoderInterface",
        "model.couplerSystem",
        "description",
        "releaseDate",
        "uvp.amount",
        "uvp.currency",
        "source.url",
        "source.notes",
        "source.imageUrl",
        "setNumber",
    }
)

ALLOWED_LIST_PATHS: frozenset[str] = frozenset(
    {
        "categories",
        "tags",
        "model.features",
    }
)


def assert_allowed_set_path(path: str) -> None:
    if path in ALLOWED_SET_PATHS or path in ALLOWED_LIST_PATHS:
        return
    raise ValueError(
        f"path not allowed for set-field/patch: {path!r}. "
        f"Allowed scalars: {sorted(ALLOWED_SET_PATHS)}; lists: {sorted(ALLOWED_LIST_PATHS)}"
    )
