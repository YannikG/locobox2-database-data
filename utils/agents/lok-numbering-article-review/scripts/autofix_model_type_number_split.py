#!/usr/bin/env python3
"""
Autofix: split combined ``model.type`` into ``model.type`` + ``model.number``.

Conservative, allowlist-only rules aligned with
``.agents/skills/lok-numbering-article-review/internal/field-parsing-model.md``
and ``SKILL.md`` (Auto-Fix Splitting).

* Only runs when ``model.number`` is null (no overwrites of explicit numbers).
* Skips ``model.type`` that contain marketing quotes (``„"«»``) or are very long.
* Optional steam rule requires ``dampflokomotive`` + URL slug confirmation.
* ``BR-<digits> <digits>`` (z. B. Roco PMT «BR-232 049») → ``type`` = Baureihe, ``number`` = Betriebsnummer.
* Drei- oder vierstellige Reihe + ``NNN-d`` + optionaler Taufname in ``„"«`` am Ende des ``type``-Strings (z. B. «1116 238-7 „Railjet"», «193 459-5 „Deutschlandpiercer"»).

Usage::

    python3 utils/agents/lok-numbering-article-review/scripts/autofix_model_type_number_split.py --dry-run articles/roco
    python3 utils/agents/lok-numbering-article-review/scripts/autofix_model_type_number_split.py --apply articles/roco
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

Article = dict[str, Any]
Proposal = tuple[str, str, str]  # rule_id, new_type, new_number


def _type_str(model: dict[str, Any]) -> Optional[str]:
    t = model.get("type")
    if not isinstance(t, str):
        return None
    s = t.strip()
    return s or None


def _number_missing(model: dict[str, Any]) -> bool:
    n = model.get("number")
    if n is None:
        return True
    if isinstance(n, str) and not n.strip():
        return True
    return False


def _skip_type_marketing(t: str) -> bool:
    return any(ch in t for ch in ("„", '"', "«", "»"))


def _rule_steam_2_4(article: Article) -> Optional[Proposal]:
    """``NN NNNN`` + dampflokomotive + slug fragment ``-NN-NNNN-``."""
    model = article.get("model") or {}
    t = _type_str(model)
    if not t or not _number_missing(model):
        return None
    m = re.fullmatch(r"(\d{2}) (\d{4})", t)
    if not m:
        return None
    cats = article.get("categories") or []
    if not isinstance(cats, list) or "dampflokomotive" not in cats:
        return None
    url = ((article.get("source") or {}).get("url") or "").lower()
    br, num = m.group(1), m.group(2)
    needle = f"-{br}-{num}-"
    if needle in url.replace("_", "-"):
        return ("steam_2_4_slug", br, num)
    return None


_BR_CLASS = re.compile(r"BR (\d+)$")


def _apply_regex_rules(t: str) -> Optional[Proposal]:
    """Deterministic regex allowlist (order: specific before generic)."""
    m = re.fullmatch(r"T (\d{3}) (\d{4})", t)
    if m:
        return ("t_3_4", f"T {m.group(1)}", m.group(2))

    m = re.fullmatch(r"E 44 (\d{3})", t)
    if m:
        return ("e_44_3", "E 44", m.group(1))

    m = re.fullmatch(r"E 469\.1(\d{3})", t)
    if m:
        return ("e_469_1_3", "E 469.1", m.group(1))

    m = re.fullmatch(r"Rc 4 (\d{4})", t)
    if m:
        return ("rc_4_4", "Rc 4", m.group(1))

    m = re.fullmatch(r"Re 4/4 III (\d+)", t)
    if m:
        return ("re_44_iii", "Re 4/4 III", m.group(1))

    m = re.fullmatch(r"Da (\d+)", t)
    if m:
        return ("da_n", "Da", m.group(1))

    m = re.fullmatch(r"Rh (\d+)", t)
    if m:
        return ("rh_n", "Rh", m.group(1))

    m = re.fullmatch(r"(Re 620) (\d{3}-\d)", t)
    if m:
        return ("re_620_dash", m.group(1), m.group(2))

    m = re.fullmatch(r"(Re 4/4 II) (\d+)", t)
    if m:
        return ("re_44_ii", m.group(1), m.group(2))

    m = re.fullmatch(r"(Re 6/6) (\d+)", t)
    if m:
        return ("re_66", m.group(1), m.group(2))

    m = re.fullmatch(r"(Re \d{3}) (\d{3}-\d)", t)
    if m:
        return ("re_3_dash", m.group(1), m.group(2))

    m = re.fullmatch(r"(BB|CC) (\d{5})", t)
    if m:
        return ("sncf_bb_cc_5", m.group(1), m.group(2))

    m = re.fullmatch(r"Y (\d{4,5})", t)
    if m:
        return ("y_n", "Y", m.group(1))

    m = re.fullmatch(r"M62-(\d+)", t)
    if m:
        return ("m62_dash", "M62", m.group(1))

    # z. B. «BR-232 049» (PMT / Roco-Slug): Baureihe ohne «BR-»-Präfix, Nummer separat
    m = re.fullmatch(r"BR-(\d+) (\d+)", t)
    if m:
        return ("br_hyphen_nn", m.group(1), m.group(2))

    m = re.fullmatch(r"(\d{3}) (\d{3}-\d)", t)
    if m:
        return ("uic_3_dash", m.group(1), m.group(2))

    return None


def _rule_4digit_3dash_taufname(t: str) -> Optional[Proposal]:
    """
    Vierstellige Baureihe + ``NNN-d`` + optionaler Taufname in Typografik-Anführungszeichen
    (z. B. ÖBB «1116 238-7 „Railjet"»), trotz ``_skip_type_marketing``.
    """
    t_st = t.strip()
    m = re.match(
        r"^(\d{4})\s+(\d{3}-\d)(?:\s+[\u201e\u201c\u00ab\"].+)?$",
        t_st,
    )
    if not m:
        return None
    return ("series_4_3dash_tail", m.group(1), m.group(2))


def _rule_3digit_3dash_taufname(t: str) -> Optional[Proposal]:
    """
    Dreistellige Baureihe + ``NNN-d`` + optionaler Taufname in Typografik-Anführungszeichen
    (z. B. «193 459-5 „Deutschlandpiercer"»), trotz ``_skip_type_marketing``.
    """
    t_st = t.strip()
    m = re.match(
        r"^(\d{3})\s+(\d{3}-\d)(?:\s+[\u201e\u201c\u00ab\"].+)?$",
        t_st,
    )
    if not m:
        return None
    return ("series_3_3dash_tail", m.group(1), m.group(2))


def propose_split(article: Article, *, include_br: bool = False) -> Optional[Proposal]:
    model = article.get("model") or {}
    t = _type_str(model)
    if not t or not _number_missing(model):
        return None
    if len(t) > 72:
        return None

    steam = _rule_steam_2_4(article)
    if steam:
        return steam

    tauf4 = _rule_4digit_3dash_taufname(t)
    if tauf4:
        return tauf4
    tauf3 = _rule_3digit_3dash_taufname(t)
    if tauf3:
        return tauf3

    if not _skip_type_marketing(t):
        p = _apply_regex_rules(t)
        if p:
            return p

    if include_br and not _skip_type_marketing(t):
        m = _BR_CLASS.fullmatch(t)
        if m:
            return ("br_class", "BR", m.group(1))

    return None


def iter_article_json_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.json") if p.is_file())


def load_article(path: Path) -> Article:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_article(path: Path, data: Article) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("articles")],
        help="Files or directories of article JSON (default: articles)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes only (default if neither --apply nor --dry-run)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write updated JSON",
    )
    ap.add_argument(
        "--include-br",
        action="store_true",
        help="Also split ``BR 110`` style into type ``BR`` + number (off by default).",
    )
    args = ap.parse_args(argv)

    if args.apply and args.dry_run:
        print("error: use only one of --apply or --dry-run", file=sys.stderr)
        return 2

    dry_run = not args.apply

    files: list[Path] = []
    for raw in args.paths:
        p = raw if raw.is_absolute() else Path.cwd() / raw
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(iter_article_json_files(p))
        else:
            print(f"error: not found: {p}", file=sys.stderr)
            return 1

    changed: list[tuple[Path, str, str, str, str, str]] = []
    for path in files:
        data = load_article(path)
        model = data.get("model")
        if not isinstance(model, dict):
            continue
        old_t = model.get("type")
        old_n = model.get("number")
        prop = propose_split(data, include_br=args.include_br)
        if not prop:
            continue
        rule_id, new_t, new_n = prop
        if old_t == new_t and old_n == new_n:
            continue
        changed.append(
            (path, rule_id, str(old_t), str(old_n), new_t, new_n)
        )
        if not dry_run:
            model["type"] = new_t
            model["number"] = new_n
            save_article(path, data)

    for path, rule_id, ot, on, nt, nn in changed:
        print(f"{path}\t{rule_id}\t{ot!r} / {on!r} -> {nt!r} / {nn!r}")

    if dry_run and changed:
        print(
            f"\n{len(changed)} file(s) would change; re-run with --apply to write.",
            file=sys.stderr,
        )
    elif dry_run:
        print("No changes.", file=sys.stderr)
    else:
        print(f"Updated {len(changed)} file(s).", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
