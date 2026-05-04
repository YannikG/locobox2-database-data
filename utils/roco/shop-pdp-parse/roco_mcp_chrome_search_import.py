#!/usr/bin/env python3
"""
Roco Shop: Artikelnummern per **Chrome-DevTools-MCP** (stdio) suchen, PDP-HTML holen,
dann ``roco_shop_parse_pdp.py`` mit ``--html-file`` + ``--canonical-url`` aufrufen.
Bei ``--merge-config`` / ``--merge-only`` wird nur ein **kompaktes** HTML (alle Spec-Tabellen + ``og:url``
+ ``og:title``) serialisiert, damit MCP die LüP-Tabelle nicht abschneidet und du bei erweiterter
``mergeOnly``-Liste (z. B. ``model.type``) den Titel parsen kannst.
Nach der PDP: zuerst **``og:image`` aus dem live DOM** (``evaluate_script``),
sonst **MCP list_network_requests** (Typ ``image``, Katalogpfade). Ergebnis als ``--image-url``
an den Parser. Netzwerkteil abschalten: ``--no-network-image`` (DOM bleibt aktiv).

Damit automatisierst du Suche, PDP und Parser-Aufruf **ohne** LLM-Token. Voraussetzung: [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
und ein **selbst gestarteter** Chrome-DevTools-MCP-Server (dieselbe ``command``/``args`` wie in
Cursor, aber als **eigener** Subprozess; die laufende Cursor-Session wird nicht angebunden).

Optional: ``--mcp-from-cursor`` liest ``~/.cursor/mcp.json`` und den Eintrag ``mcpServers.chrome-devtools``
(oder ``--mcp-cursor-server``), damit du keine separate JSON-Array-Datei brauchst. Dabei wird standardmässig
``--isolated`` an ``chrome-devtools-mcp`` angehängt, damit parallel zu Cursor kein Profil-Konflikt entsteht
(abschalten: ``--no-chrome-isolated``).

**Python:** mindestens **3.10**. Abhängigkeiten: ``pip install -r utils/requirements.txt`` (``mcp`` darin per PEP-508 nur für ``python_version >= "3.10"``).

Installation (empfohlen mit venv, Repo-Root)::

    python3.12 -m venv .venv && source .venv/bin/activate
    pip install -r utils/requirements.txt

Stdio-Kommando (JSON-Array) in einer Datei, z. B. ``chrome-mcp-stdio.json``::

    [\"npx\", \"-y\", \"<dein-chrome-devtools-mcp-paket>\", \"...\"]

Aufruf (Repo-Root), Konfig wie in Cursor (ohne Extra-Datei)::

    python3 utils/roco/shop-pdp-parse/roco_mcp_chrome_search_import.py \\
      --articles artikel.txt \\
      --mcp-from-cursor \\
      --start-url \"https://www.roco.cc/\"

Nur Spec-Felder (LüP, Mindestradius, Stromsystem, …) überschreiben::

    python3 utils/roco/shop-pdp-parse/roco_mcp_chrome_search_import.py \\
      --articles artikel.txt \\
      --mcp-from-cursor \\
      --merge-config utils/roco/shop-pdp-parse/merge-pdp-specs-fields.json

Typ/Nummer/Betreiber aus ``og:title`` mit derselben Logik wie der Parser: eigene JSON mit erweiterter
``mergeOnly`` (siehe ``merge-pdp-specs-with-title-model.json``) oder bestehende Datei anpassen.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PARSER = _REPO_ROOT / "utils" / "roco" / "shop-pdp-parse" / "roco_shop_parse_pdp.py"
_DEFAULT_START = "https://www.roco.cc/"
_TMP_HTML = _REPO_ROOT / ".tmp" / "roco-mcp-pdp"


def _load_mcp_stdio_argv(path: Optional[Path]) -> list[str]:
    raw = os.environ.get("ROCO_CHROME_MCP_STDIO_JSON", "").strip()
    if path is not None:
        p = path.expanduser().resolve()
        if not p.is_file():
            print(
                f"error: Datei fehlt oder ist kein File: {path}\n"
                "Hinweis: «PFAD/ZU/…» war nur ein Platzhalter. Echte Datei anlegen oder "
                "--mcp-from-cursor nutzen (liest ~/.cursor/mcp.json).",
                file=sys.stderr,
            )
            raise SystemExit(2)
        raw = p.read_text(encoding="utf-8").strip()
    if not raw:
        print(
            "error: Stdio-Kommando fehlt. Optionen: --mcp-from-cursor (Cursor-Konfiguration), "
            "oder JSON-Array in einer Datei mit --mcp-stdio-json, "
            "oder Umgebung ROCO_CHROME_MCP_STDIO_JSON.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    data = json.loads(raw)
    if not isinstance(data, list) or len(data) < 1 or not all(isinstance(x, str) for x in data):
        print("error: MCP-stdio muss ein JSON-Array aus mindestens einem String sein.", file=sys.stderr)
        raise SystemExit(2)
    return list(data)


def _cursor_stdio_argv_and_env(
    config_path: Path, server_name: str
) -> tuple[list[str], dict[str, str]]:
    """
    Liest einen stdio-Server aus Cursors ``mcp.json`` (``mcpServers.<name>``).
    URL-only-Server (ohne ``command``) werden nicht unterstützt.
    """
    if not config_path.is_file():
        print(f"error: Cursor-MCP-Konfig fehlt: {config_path}", file=sys.stderr)
        raise SystemExit(2)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers") or {}
    ent = servers.get(server_name)
    if not isinstance(ent, dict):
        print(
            f"error: in {config_path} fehlt oder ist ungültig: mcpServers[{server_name!r}]",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if ent.get("url"):
        print(
            "error: dieser MCP-Server nutzt «url», nicht stdio. "
            "Nur Einträge mit «command» (wie chrome-devtools) werden unterstützt.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    cmd = ent.get("command")
    if not cmd:
        print("error: MCP-Server-Eintrag ohne «command».", file=sys.stderr)
        raise SystemExit(2)
    cmd_s = str(cmd).strip()
    args = ent.get("args") or []
    env_raw = ent.get("env") or {}
    if isinstance(args, list) and len(args) > 0:
        argv = [cmd_s] + [str(a) for a in args]
    else:
        argv = shlex.split(cmd_s)
    if not argv:
        print("error: leeres Kommando nach dem Parsen der Cursor-MCP-Konfig.", file=sys.stderr)
        raise SystemExit(2)
    env_out: dict[str, str] = {}
    if isinstance(env_raw, dict):
        for k, v in env_raw.items():
            if v is None:
                continue
            vs = str(v).strip()
            if vs:
                env_out[str(k)] = vs
    return argv, env_out


def _tool_text(result: Any) -> str:
    """Ersten Textblock aus ``CallToolResult`` lesen."""
    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        t = getattr(block, "type", None)
        if t == "text":
            parts.append(getattr(block, "text", "") or "")
    return "\n".join(parts).strip()


def _mcp_evaluate_script_return_text(raw: str) -> str:
    """
    Chrome-DevTools-MCP formatiert ``evaluate_script`` oft als Fliesstext plus
    ``Script ran on page … returned:`` und Markdown-Codeblock. Ohne diese
    Entpackung landet der Präfix im ``--html-file`` und der Parser findet keine
    Tabellen (LüP bleibt leer).
    """
    t = (raw or "").strip()
    if "Script ran on page" in t:
        rest = t.split("Script ran on page", 1)[-1].strip()
        if "returned:" in rest.lower():
            t = rest.split("returned:", 1)[-1].strip()
        else:
            t = rest
    m_fence = re.search(r"```(?:json|html)?\s*\n?(.*?)```", t, re.S | re.I)
    if m_fence:
        inner = m_fence.group(1).strip()
        try:
            out = json.loads(inner)
            if isinstance(out, str):
                return out
        except json.JSONDecodeError:
            pass
        return inner
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        try:
            out = json.loads(t)
            if isinstance(out, str):
                return out
        except json.JSONDecodeError:
            pass
    return t


def _tool_content_dump(result: Any) -> str:
    """Alle MCP-Content-Blöcke serialisieren (für pageId in Text- oder Resource-Blöcken)."""
    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        dump = getattr(block, "model_dump_json", None)
        if callable(dump):
            try:
                parts.append(dump())
                continue
            except Exception:
                pass
        t = getattr(block, "type", None)
        if t == "text":
            parts.append(getattr(block, "text", "") or "")
        else:
            parts.append(str(block))
    return "\n".join(parts).strip()


def _eval_scalar(text: str) -> str:
    """Wert aus ``evaluate_script`` normalisieren (reiner String, JSON-String, MCP-Markdown)."""
    t = (text or "").strip()
    if not t:
        return t
    if "Script ran on page" in t:
        after = t.split("Script ran on page", 1)[-1]
        if "returned:" in after.lower():
            t = after.split("returned:", 1)[-1].strip()
        else:
            t = after.strip()
    m_fence = re.search(r"```(?:json)?\s*\n?(.*?)```", t, re.S | re.I)
    if m_fence:
        inner = m_fence.group(1).strip()
        try:
            out = json.loads(inner)
            if isinstance(out, str):
                return out
        except json.JSONDecodeError:
            if inner.startswith(("http://", "https://")):
                return inner.split()[0].rstrip(".,);")
    if len(t) >= 2 and ((t[0] == t[-1] == '"') or (t[0] == t[-1] == "'")):
        try:
            out = json.loads(t)
            if isinstance(out, str):
                return out
        except json.JSONDecodeError:
            pass
    m_url = re.search(r"https?://[^\s`'\"<>]+", t)
    if m_url:
        return m_url.group(0).rstrip(".,);")
    return t


def _tool_raise(name: str, result: Any) -> None:
    if getattr(result, "isError", False):
        print(f"error: MCP-Tool {name}: {_tool_text(result)}", file=sys.stderr)
        raise SystemExit(1)


def _guess_page_id(list_text: str) -> int:
    raw = (list_text or "").strip()
    if not raw:
        return 0
    # MCP-JSON-Dump einer Textzeile: «"text":"## Pages\n1: …"» → lesbarer Text
    if '"text"' in raw and raw.lstrip().startswith("{"):
        try:
            outer = json.loads(raw)
            if isinstance(outer, dict) and isinstance(outer.get("text"), str):
                raw = outer["text"]
        except json.JSONDecodeError:
            pass

    lines = re.split(r"\r\n|\n|\\n", raw)

    def _from_obj(data: Any) -> Optional[int]:
        if isinstance(data, dict):
            for k in ("pageId", "page_id", "id"):
                v = data.get(k)
                if isinstance(v, bool):
                    continue
                if isinstance(v, int):
                    return int(v)
                if isinstance(v, str) and v.strip().isdigit():
                    return int(v.strip())
            pages = data.get("pages")
            if isinstance(pages, list) and pages and isinstance(pages[0], dict):
                return _from_obj(pages[0])
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                return _from_obj(data[0])
        return None

    chunks: list[str] = [raw]
    if "```" in raw:
        parts = raw.split("```")
        for i, part in enumerate(parts):
            p = part.strip()
            if p.lower().startswith("json"):
                p = p[4:].lstrip().strip()
            if p.startswith("{") or p.startswith("["):
                chunks.append(p)
    for chunk in chunks:
        try:
            data = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        got = _from_obj(data)
        if got is not None:
            return got

    # chrome-devtools-mcp: «## Pages» / «2: https://… [selected]» (Nummer = pageId)
    sel: Optional[int] = None
    last_num: Optional[int] = None
    for line in lines:
        mline = re.match(r"^\s*(\d+)\s*:", line)
        if mline:
            n = int(mline.group(1))
            last_num = n
            if "[selected]" in line.lower():
                sel = n
    if sel is not None:
        return sel
    if last_num is not None:
        return last_num

    m = re.search(r'"pageId"\s*:\s*(\d+)', raw)
    if m:
        return int(m.group(1))
    m = re.search(r'"id"\s*:\s*(\d+)', raw)
    if m:
        return int(m.group(1))
    m = re.search(r"\(?pageId\s*[:=]\s*(\d+)\)?", raw, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"pageId\D+(\d+)", raw, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"\bid\s*[=:]\s*(\d+)\b", raw, re.I)
    if m:
        return int(m.group(1))
    return 0


def _is_pdp_url(href: str, article: str) -> bool:
    u = href.split("?", 1)[0].lower()
    needle = f"/{article}-".lower()
    return needle in u and u.endswith(".html")


def _js_search_submit(article: str) -> str:
    if not article.isdigit():
        raise ValueError("Artikelnummer nur Ziffern")
    return f"""() => {{
  const art = "{article}";
  const el = document.querySelector('#search, input[name="q"]');
  if (!el) return {{"err": "no_search_input"}};
  el.focus();
  el.value = art;
  el.dispatchEvent(new Event("input", {{ bubbles: true }}));
  if (el.form) {{
    el.form.requestSubmit();
  }} else {{
    el.dispatchEvent(new KeyboardEvent("keydown", {{ key: "Enter", bubbles: true }}));
  }}
  return {{"ok": true}};
}}"""


def _js_click_first_pdp_link(article: str) -> str:
    if not article.isdigit():
        raise ValueError("Artikelnummer nur Ziffern")
    return f"""() => {{
  const art = "{article}";
  const links = Array.from(document.querySelectorAll('a[href*="/' + art + '-"]'));
  const hit = links.find((a) => a.href && a.href.includes(".html"));
  if (!hit) return {{"err": "no_pdp_link"}};
  hit.click();
  return {{"ok": true}};
}}"""


def _js_outer_html() -> str:
    return "() => document.documentElement.outerHTML"


def _js_compact_pdp_html() -> str:
    """
    Kleines Dokument mit ``og:url``, ``og:title`` (Meta oder ``document.title``) und allen
    ``table#product-attribute-specs-table``. Für selektiven Merge inkl. Titel-Felder nötig.
    """
    return """() => {
  const esc = (s) => String(s)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  const href = String(location.href || '').split('#')[0];
  let head = '<meta property="og:url" content="' + esc(href) + '" />';
  const ogTitleEl = document.querySelector('meta[property="og:title"]');
  const titleC = ogTitleEl && ogTitleEl.getAttribute('content');
  if (titleC && String(titleC).trim()) {
    head += '<meta property="og:title" content="' + esc(String(titleC).trim()) + '" />';
  } else {
    const dt = document.title;
    if (dt && String(dt).trim()) {
      head += '<meta property="og:title" content="' + esc(String(dt).trim()) + '" />';
    }
  }
  const tables = Array.from(document.querySelectorAll('table#product-attribute-specs-table'))
    .map((t) => t.outerHTML)
    .join('');
  return '<!DOCTYPE html><html><head>' + head + '</head><body>' + tables + '</body></html>';
}"""


def _js_location_href() -> str:
    return "() => location.href"


def _js_og_image_from_dom() -> str:
    """Gleiche Session wie der Skill: Meta ``og:image`` aus dem live DOM (nicht nur Regex auf outerHTML)."""
    return """() => {
  const metas = Array.from(document.querySelectorAll('meta[property]'));
  for (const el of metas) {
    const p = (el.getAttribute('property') || '').toLowerCase();
    if (p === 'og:image' || p === 'og:image:url' || p === 'og:image:secure_url') {
      const c = el.getAttribute('content');
      if (c && String(c).trim().length > 8) return String(c).trim();
    }
  }
  return null;
}"""


_ROCO_CATALOG_IMG_RE = re.compile(
    r"https://(?:www\.)?roco\.cc/media/catalog/product/[^\s\"'`\])>]+",
    re.I,
)


def _pick_roco_catalog_image_url(urls: list[str], article: str) -> Optional[str]:
    """
    Aus Netzwerk- oder Textdump: beste URL unter ``/media/catalog/product/`` wählen
    (Hauptbild, keine Platzhalter/Logos).
    """
    seen: set[str] = set()
    uniq: list[str] = []
    for raw_u in urls:
        u = raw_u.rstrip(".,);")
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(u)

    def score(u: str) -> tuple[float, int]:
        ul = u.lower()
        s = 0.0
        if "/media/catalog/product/" in ul:
            s += 200.0
        if "/cache/" in ul:
            s += 80.0
        if article and article in u:
            s += 40.0
        if any(bad in ul for bad in ("placeholder", "/logo", "icon", "sprite", "/wysiwyg/")):
            s -= 500.0
        return (s, len(u))

    good = [u for u in uniq if "roco.cc" in u.lower() and "/media/catalog/product/" in u.lower()]
    if not good:
        return None
    good.sort(key=lambda u: score(u), reverse=True)
    return good[0]


async def _mcp_catalog_image_from_network(session: Any, article: str) -> Optional[str]:
    """Chrome-DevTools-MCP: ``list_network_requests`` (Typ image), Katalog-Bild-URL wählen."""
    try:
        res = await session.call_tool(
            "list_network_requests",
            {
                "resourceTypes": ["image"],
                "includePreservedRequests": True,
            },
        )
    except Exception as ex:
        print(f"warning: list_network_requests nicht aufgerufen: {ex}", file=sys.stderr)
        return None
    if getattr(res, "isError", False):
        print(f"warning: list_network_requests: {_tool_text(res)}", file=sys.stderr)
        return None
    raw = _tool_content_dump(res)
    found = list(_ROCO_CATALOG_IMG_RE.findall(raw))
    found.extend(
        re.findall(
            r'"url"\s*:\s*"(https://(?:www\.)?roco\.cc/media/catalog/product/[^"]+)"',
            raw,
            re.I,
        )
    )
    return _pick_roco_catalog_image_url(found, article)


def _read_article_numbers(path: Path) -> list[str]:
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.isdigit() and 5 <= len(line) <= 8:
            out.append(line)
        else:
            print(f"warning: Zeile übersprungen (keine 5–8 stellige Nummer): {line!r}", file=sys.stderr)
    return out


async def _run_mcp_import(
    *,
    mcp_argv: list[str],
    mcp_extra_env: Optional[dict[str, str]],
    articles: list[str],
    start_url: str,
    page_id: Optional[int],
    delay_s: float,
    write: bool,
    notes: str,
    dry_run: bool,
    use_network_image: bool,
    merge_config: Optional[Path],
    merge_only: Optional[list[str]],
) -> tuple[int, int]:
    if sys.version_info < (3, 10):
        print(
            "error: Python 3.10 oder neuer nötig. Das Paket «mcp» listet keine Releases für ältere "
            "Interpreter. Bitte z. B. python3.12/python3.11 nutzen und damit pip install ausführen.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        print(
            "error: Paket «mcp» fehlt. Repo-Root: pip install -r utils/requirements.txt (Python >= 3.10). "
            "SDK: https://github.com/modelcontextprotocol/python-sdk",
            file=sys.stderr,
        )
        raise SystemExit(2) from None

    cmd = mcp_argv[0]
    args = mcp_argv[1:]
    merged_env = os.environ.copy()
    if mcp_extra_env:
        merged_env.update(mcp_extra_env)
    server = StdioServerParameters(command=cmd, args=args, env=merged_env)

    ok = 0
    fail = 0

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            lp = await session.call_tool("list_pages", {})
            _tool_raise("list_pages", lp)
            lp_dump = _tool_content_dump(lp)
            last_dump = lp_dump
            pid = page_id if page_id is not None else _guess_page_id(lp_dump)
            if pid <= 0:
                np = await session.call_tool(
                    "new_page",
                    {"url": start_url, "timeout": 60000},
                )
                _tool_raise("new_page", np)
                np_dump = _tool_content_dump(np)
                last_dump = np_dump or last_dump
                pid = page_id if page_id is not None else _guess_page_id(np_dump)
                await asyncio.sleep(max(0.5, min(delay_s, 3.0)))
                if pid <= 0:
                    lp = await session.call_tool("list_pages", {})
                    _tool_raise("list_pages", lp)
                    lp_dump = _tool_content_dump(lp)
                    last_dump = lp_dump or last_dump
                    pid = page_id if page_id is not None else _guess_page_id(lp_dump)
            if pid <= 0:
                hint = (last_dump or "")[:800]
                print(
                    "error: keine pageId aus MCP-Antwort (list_pages / new_page). "
                    "--page-id setzen oder Chrome-Ausgabe prüfen. Rohausschnitt:\n"
                    f"{hint}",
                    file=sys.stderr,
                )
                raise SystemExit(1)
            sp = await session.call_tool("select_page", {"pageId": pid, "bringToFront": True})
            _tool_raise("select_page", sp)

            for art in articles:
                print(f"-- {art}", flush=True)
                try:
                    nav = await session.call_tool(
                        "navigate_page",
                        {"type": "url", "url": start_url, "timeout": 60000},
                    )
                    _tool_raise("navigate_page", nav)
                    await asyncio.sleep(delay_s)

                    ev = await session.call_tool(
                        "evaluate_script",
                        {"function": _js_search_submit(art)},
                    )
                    _tool_raise("evaluate_script", ev)
                    body = _tool_text(ev)
                    if '"err"' in body and "no_search_input" in body:
                        print(f"error: {art}: Suchfeld nicht gefunden", file=sys.stderr)
                        fail += 1
                        continue

                    await asyncio.sleep(delay_s)
                    try:
                        wf = await session.call_tool(
                            "wait_for",
                            {"text": [art], "timeout": 45000},
                        )
                        _tool_raise("wait_for", wf)
                    except Exception as ex:
                        print(f"warning: wait_for: {ex}", file=sys.stderr)

                    href_ev = await session.call_tool(
                        "evaluate_script",
                        {"function": _js_location_href()},
                    )
                    _tool_raise("evaluate_script", href_ev)
                    href = _eval_scalar(_tool_text(href_ev))

                    if not _is_pdp_url(href, art):
                        clk = await session.call_tool(
                            "evaluate_script",
                            {"function": _js_click_first_pdp_link(art)},
                        )
                        _tool_raise("evaluate_script", clk)
                        await asyncio.sleep(delay_s)
                        try:
                            wf2 = await session.call_tool(
                                "wait_for",
                                {"text": [art], "timeout": 45000},
                            )
                            _tool_raise("wait_for", wf2)
                        except Exception as ex:
                            print(f"warning: wait_for (nach Klick): {ex}", file=sys.stderr)
                        href_ev = await session.call_tool(
                            "evaluate_script",
                            {"function": _js_location_href()},
                        )
                        _tool_raise("evaluate_script", href_ev)
                        href = _eval_scalar(_tool_text(href_ev))

                    if not _is_pdp_url(href, art):
                        print(f"error: {art}: keine PDP-URL (nach Suche/Klick): {href!r}", file=sys.stderr)
                        fail += 1
                        continue

                    await asyncio.sleep(max(0.3, min(1.5, delay_s * 0.5)))
                    image_url_override: Optional[str] = None
                    og_ev = await session.call_tool(
                        "evaluate_script",
                        {"function": _js_og_image_from_dom()},
                    )
                    _tool_raise("evaluate_script", og_ev)
                    og_raw = _eval_scalar(_tool_text(og_ev))
                    if isinstance(og_raw, str):
                        u = og_raw.strip()
                        if u.lower() not in ("", "null", "undefined") and u.startswith(("http://", "https://")):
                            image_url_override = u.split()[0].strip()
                    if not image_url_override and use_network_image:
                        await asyncio.sleep(max(0.3, min(1.5, delay_s * 0.5)))
                        image_url_override = await _mcp_catalog_image_from_network(session, art)

                    use_compact_html = merge_config is not None or bool(merge_only)
                    if use_compact_html:
                        try:
                            wf_spec = await session.call_tool(
                                "wait_for",
                                {
                                    "text": [
                                        "Länge über Puffer",
                                        "Mindestradius",
                                        "Abmessungen",
                                    ],
                                    "timeout": 15000,
                                },
                            )
                            if getattr(wf_spec, "isError", False):
                                print(
                                    f"warning: {art}: wait_for Spec-Tabelle: {_tool_text(wf_spec)}",
                                    file=sys.stderr,
                                )
                        except Exception as ex:
                            print(f"warning: {art}: wait_for Spec-Tabelle: {ex}", file=sys.stderr)
                        html_ev = await session.call_tool(
                            "evaluate_script",
                            {"function": _js_compact_pdp_html()},
                        )
                        _tool_raise("evaluate_script", html_ev)
                        html = _mcp_evaluate_script_return_text(_tool_text(html_ev))
                        if (
                            not html
                            or "product-attribute-specs-table" not in html
                            or len(html) < 80
                        ):
                            print(
                                f"warning: {art}: compactes Spec-HTML unzureichend, "
                                "Fallback auf documentElement.outerHTML",
                                file=sys.stderr,
                            )
                            html_ev = await session.call_tool(
                                "evaluate_script",
                                {"function": _js_outer_html()},
                            )
                            _tool_raise("evaluate_script", html_ev)
                            html = _mcp_evaluate_script_return_text(_tool_text(html_ev))
                    else:
                        html_ev = await session.call_tool(
                            "evaluate_script",
                            {"function": _js_outer_html()},
                        )
                        _tool_raise("evaluate_script", html_ev)
                        html = _mcp_evaluate_script_return_text(_tool_text(html_ev))
                    if not html:
                        print(f"error: {art}: HTML leer", file=sys.stderr)
                        fail += 1
                        continue
                    if not use_compact_html and len(html) < 500:
                        print(f"error: {art}: HTML zu kurz (volle Seite)", file=sys.stderr)
                        fail += 1
                        continue
                    if use_compact_html and len(html) < 80:
                        print(f"error: {art}: HTML zu kurz (auch nach Fallback)", file=sys.stderr)
                        fail += 1
                        continue

                    if dry_run:
                        ni = f" image={image_url_override!r}" if image_url_override else ""
                        print(f"dry-run: {art} canon={href!r} html_len={len(html)}{ni}")
                        ok += 1
                        continue

                    _TMP_HTML.mkdir(parents=True, exist_ok=True)
                    html_path = (_TMP_HTML / f"{art}.html").resolve()
                    html_path.write_text(html, encoding="utf-8", errors="replace")

                    pargs = [
                        sys.executable,
                        str(_PARSER),
                        "--html-file",
                        str(html_path),
                        "--canonical-url",
                        href,
                        "--article",
                        art,
                        "--notes",
                        notes,
                    ]
                    if image_url_override:
                        pargs.extend(["--image-url", image_url_override])
                    if merge_config is not None:
                        pargs.extend(["--merge-config", str(merge_config)])
                    if merge_only:
                        for chunk in merge_only:
                            if str(chunk).strip():
                                pargs.extend(["--merge-only", str(chunk).strip()])
                    if write:
                        pargs.extend(["--write", "--quiet"])
                    try:
                        proc = subprocess.run(
                            pargs,
                            cwd=str(_REPO_ROOT),
                            timeout=300,
                        )
                    except subprocess.TimeoutExpired:
                        print(f"error: Parser-Zeitüberschreitung (300s) für {art}", file=sys.stderr)
                        fail += 1
                        continue
                    if proc.returncode != 0:
                        print(f"error: Parser exit {proc.returncode} für {art}", file=sys.stderr)
                        fail += 1
                    else:
                        ok += 1
                except SystemExit:
                    raise
                except Exception as ex:
                    print(f"error: {art}: {ex}", file=sys.stderr)
                    fail += 1

                await asyncio.sleep(delay_s)

    print(json.dumps({"ok": ok, "fail": fail}, ensure_ascii=False))
    return ok, fail


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Roco PDP-Import über Chrome-DevTools-MCP (stdio) + roco_shop_parse_pdp.py",
    )
    ap.add_argument(
        "--articles",
        type=Path,
        required=True,
        help="Textdatei: eine Artikelnummer (5–8 Ziffern) pro Zeile, # Kommentare.",
    )
    ap.add_argument(
        "--mcp-from-cursor",
        action="store_true",
        help="Stdio aus ~/.cursor/mcp.json (mcpServers) laden; schliesst --mcp-stdio-json / ROCO_* aus.",
    )
    ap.add_argument(
        "--mcp-cursor-config",
        type=Path,
        default=Path.home() / ".cursor" / "mcp.json",
        help="Pfad zu Cursors mcp.json (nur mit --mcp-from-cursor).",
    )
    ap.add_argument(
        "--mcp-cursor-server",
        default="chrome-devtools",
        help="Schlüssel unter mcpServers (default: chrome-devtools). Nur mit --mcp-from-cursor.",
    )
    ap.add_argument(
        "--no-chrome-isolated",
        action="store_true",
        help="Kein «--isolated» an chrome-devtools-mcp (nur bei --mcp-from-cursor). Standard: "
        "«--isolated» anhängen, damit kein Konflikt mit einem schon laufenden MCP-Chrome (z. B. Cursor).",
    )
    ap.add_argument(
        "--mcp-stdio-json",
        type=Path,
        default=None,
        help="Datei mit JSON-Array: [Kommando, Arg1, …] für den MCP-Server-Start (stdio).",
    )
    ap.add_argument(
        "--start-url",
        default=_DEFAULT_START,
        help=f"Shop-Startseite (default: {_DEFAULT_START})",
    )
    ap.add_argument(
        "--page-id",
        type=int,
        default=None,
        help="Chrome-Tab pageId; default aus list_pages raten.",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Sekunden Pause zwischen Schritten / Artikeln (default: 2).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Kein Parser, nur MCP und PDP-URL prüfen.",
    )
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="Parser ohne --write (JSON auf stdout).",
    )
    ap.add_argument(
        "--notes",
        default="Daten von der Webseite, automatisch geupdated.",
        help="--notes an den Parser (bei --write).",
    )
    ap.add_argument(
        "--no-network-image",
        action="store_true",
        help="Kein list_network_requests; ``og:image`` wird weiterhin per DOM-Script gelesen.",
    )
    ap.add_argument(
        "--merge-config",
        type=Path,
        default=None,
        metavar="PATH",
        help="An roco_shop_parse_pdp.py weitergeben (nur mit --write). Relativ zum Repo-Root oder absolut.",
    )
    ap.add_argument(
        "--merge-only",
        action="append",
        default=None,
        metavar="KEYS",
        help=(
            "An roco_shop_parse_pdp.py weitergeben (mehrfach erlaubt; nur mit --write). "
            "Siehe dort --help."
        ),
    )
    args = ap.parse_args()

    mcp_extra_env: Optional[dict[str, str]] = None
    if args.mcp_from_cursor:
        if args.mcp_stdio_json is not None:
            print(
                "error: nicht gleichzeitig --mcp-from-cursor und --mcp-stdio-json.",
                file=sys.stderr,
            )
            return 2
        if os.environ.get("ROCO_CHROME_MCP_STDIO_JSON", "").strip():
            print(
                "error: nicht gleichzeitig --mcp-from-cursor und ROCO_CHROME_MCP_STDIO_JSON.",
                file=sys.stderr,
            )
            return 2
        mcp_argv, mcp_extra_env = _cursor_stdio_argv_and_env(
            args.mcp_cursor_config.expanduser().resolve(),
            str(args.mcp_cursor_server).strip() or "chrome-devtools",
        )
        if not args.no_chrome_isolated and "--isolated" not in mcp_argv:
            mcp_argv = [*mcp_argv, "--isolated"]
    else:
        mcp_argv = _load_mcp_stdio_argv(args.mcp_stdio_json)

    numbers = _read_article_numbers(args.articles.expanduser().resolve())
    if not numbers:
        print("error: keine gültigen Artikelnummern in --articles", file=sys.stderr)
        return 2

    merge_cfg = args.merge_config.expanduser().resolve() if args.merge_config else None
    if merge_cfg is not None and not merge_cfg.is_file():
        print(f"error: --merge-config nicht gefunden: {merge_cfg}", file=sys.stderr)
        return 2
    if (merge_cfg is not None or args.merge_only) and (args.no_write or args.dry_run):
        print(
            "error: --merge-config / --merge-only nur zusammen mit echtem --write "
            "(ohne --dry-run und ohne --no-write).",
            file=sys.stderr,
        )
        return 2

    _ok, fail = asyncio.run(
        _run_mcp_import(
            mcp_argv=mcp_argv,
            mcp_extra_env=mcp_extra_env,
            articles=numbers,
            start_url=args.start_url.strip(),
            page_id=args.page_id,
            delay_s=max(0.0, args.delay),
            write=not args.no_write and not args.dry_run,
            notes=args.notes,
            dry_run=args.dry_run,
            use_network_image=not args.no_network_image,
            merge_config=merge_cfg,
            merge_only=args.merge_only,
        )
    )
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
