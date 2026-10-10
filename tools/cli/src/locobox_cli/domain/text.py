from __future__ import annotations


def swiss_ss(text: str) -> str:
    """Swiss spelling: no sharp s."""
    return text.replace("\u00df", "ss").replace("ß", "ss")


def normalize_article_strings(data: dict) -> int:
    """Apply swiss_ss to all string leaves. Returns number of changed strings."""
    changed = 0

    def walk(obj: object) -> object:
        nonlocal changed
        if isinstance(obj, str):
            new = swiss_ss(obj)
            if new != obj:
                changed += 1
            return new
        if isinstance(obj, list):
            return [walk(x) for x in obj]
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        return obj

    new_data = walk(data)
    if isinstance(new_data, dict):
        data.clear()
        data.update(new_data)
    return changed
