from __future__ import annotations

import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

from locobox_cli.adapters.sources.bemo.shop_site import compact_sku, spaced_sku
from locobox_cli.domain.text import swiss_ss

_OPERATOR_COUNTRY = {
    "RhB": "CH",
    "Rhätische Bahn": "CH",
    "Rhaetische Bahn": "CH",
    "MGB": "CH",
    "Matterhorn Gotthard Bahn": "CH",
    "MOB": "CH",
    "Montreux Berner Oberland Bahn": "CH",
    "DFB": "CH",
    "Dampfbahn Furka Bergstrecke": "CH",
    "FO": "CH",
    "Furka Oberalp": "CH",
    "BVZ": "CH",
    "Brig Visp Zermatt": "CH",
    "SBB": "CH",
    "BLS": "CH",
    "DR": "DE",
    "DRG": "DE",
    "DB": "DE",
    "DB AG": "DE",
    "ÖBB": "AT",
    "OBB": "AT",
    "StLB": "AT",
    "ZB": "AT",
    "K.Sä.Sts.B.": "DE",
    "K.Sae.Sts.B.": "DE",
}

_UVP = re.compile(
    r"UVP\s*:\s*(?P<price>(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2})\s*(?:€|EUR|Euro)?",
    re.I,
)
# Meta line examples: ``H0m VI 166 R>330``, ``H0e V``, ``0m IV``
_META_LINE = re.compile(
    r"\b(?P<scale>H0m|H0e|H0|0m|0e|N|TT)\b"
    r"(?:\s+(?P<era>I{1,3}|IV|VI{0,3}|V))?\b",
    re.I,
)


def _meta(html: str, prop: str) -> Optional[str]:
    m = re.search(
        rf'<meta\s+(?:property|name)=["\']{re.escape(prop)}["\']\s+content=["\']([^"\']+)["\']',
        html,
        re.I | re.S,
    )
    if not m:
        m = re.search(
            rf'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']{re.escape(prop)}["\']',
            html,
            re.I | re.S,
        )
    return html_lib.unescape(m.group(1).strip()) if m else None


def _plain(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html_lib.unescape(t)
    return swiss_ss(re.sub(r"\s+", " ", t).strip())


def _h1(html: str) -> str:
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
    return _plain(m.group(1)) if m else ""


def _page_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([\s\S]*?)</title>", html, re.I)
    if not m:
        return ""
    t = _plain(m.group(1))
    return re.sub(r"\s*[–-]\s*BEMO Modelleisenbahnen\s*$", "", t, flags=re.I).strip()


def _product_title(html: str, article: str) -> str:
    wanted = compact_sku(article)
    for cand in (_h1(html), _page_title(html), swiss_ss(_meta(html, "og:title") or "")):
        t = re.sub(r"\s*[–-]\s*BEMO Modelleisenbahnen\s*$", "", cand or "", flags=re.I).strip()
        if not t:
            continue
        digits = compact_sku(t)
        if digits == wanted or re.fullmatch(r"\d{6,8}", t):
            continue
        return t
    return wanted


def extract_artnr(html: str) -> Optional[str]:
    """Read ``.single_artnr`` (often ``2295 561 ``) and return digits-only canonical."""
    m = re.search(
        r'class=["\'][^"\']*\bsingle_artnr\b[^"\']*["\'][^>]*>([\s\S]*?)</(?:span|div|p|td|strong)>',
        html,
        re.I,
    )
    if not m:
        return None
    digits = compact_sku(_plain(m.group(1)))
    return digits or None


def _parse_price(raw: str) -> float:
    s = re.sub(r"\.(?=\d{3},)", "", raw.strip()).replace(",", ".")
    return float(s)


def _uvp_from_html(html: str) -> Optional[float]:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    m = _UVP.search(text)
    if not m:
        return None
    try:
        return _parse_price(m.group("price"))
    except ValueError:
        return None


def _scale_era_from_text(blob: str) -> tuple[str, str]:
    scale_map = {
        "H0M": "H0m",
        "H0E": "H0e",
        "H0": "H0",
        "0M": "0m",
        "0E": "0e",
        "N": "N",
        "TT": "TT",
    }
    # Prefer a match that includes era (e.g. ``H0m VI 166``) over bare ``H0m``.
    chosen = None
    for m in _META_LINE.finditer(blob):
        if m.group("era"):
            chosen = m
            break
        if chosen is None:
            chosen = m
    if not chosen:
        return "H0m", "Unbekannt"
    scale_out = scale_map.get(chosen.group("scale").upper(), chosen.group("scale"))
    era = (chosen.group("era") or "").upper() or "Unbekannt"
    return scale_out, era


def _operator_country(blob: str) -> tuple[str, str]:
    t = swiss_ss(blob or "")
    for name in sorted(_OPERATOR_COUNTRY, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", t, re.I):
            cc = _OPERATOR_COUNTRY[name]
            canon = "ÖBB" if name == "OBB" else name
            if name in {"Rhätische Bahn", "Rhaetische Bahn"}:
                canon = "RhB"
            elif name == "Matterhorn Gotthard Bahn":
                canon = "MGB"
            elif name == "Montreux Berner Oberland Bahn":
                canon = "MOB"
            elif name == "Dampfbahn Furka Bergstrecke":
                canon = "DFB"
            elif name == "Furka Oberalp":
                canon = "FO"
            elif name == "Brig Visp Zermatt":
                canon = "BVZ"
            elif name in {"K.Sae.Sts.B.", "K.Sä.Sts.B."}:
                canon = "K.Sä.Sts.B."
            return canon, cc
    if re.search(r"K\.?\s*Sä\.?\s*Sts\.?\s*B\.?", blob, re.I) or re.search(
        r"K\.?\s*Sae\.?\s*Sts\.?\s*B\.?", blob, re.I
    ):
        return "K.Sä.Sts.B.", "DE"
    if re.search(r"\bStLB\b", blob, re.I):
        return "StLB", "AT"
    return "Unbekannt", "CH"


def _electric_from_text(blob: str) -> str:
    t = blob.lower()
    digital = bool(re.search(r"\b(digital|dcc|sound|decoder)\b", t))
    if re.search(r"\b(ac|wechselstrom|3[\s-]?leiter)\b", t):
        return "AC-Digital" if digital else "AC-Analog"
    if digital:
        return "DC-Digital"
    return "DC-Analog"


def _categories(title: str, kind_blob: str) -> list[str]:
    blob = f"{title} {kind_blob}".lower()
    if re.search(r"triebwagen|triebzug", blob):
        if re.search(r"elektro|ge\s*4|ae\s*|abe", blob):
            return ["triebwagen", "elektrotriebwagen"]
        if re.search(r"diesel", blob):
            return ["triebwagen", "dieseltriebwagen"]
        return ["triebwagen"]
    if re.search(r"\bdampf|\bdampflok|\bdr\s*99\b|\b99\s+\d{3}", blob):
        return ["lokomotive", "dampflokomotive"]
    if re.search(r"\bdiesel|\bdiesellok|\bgmf\b|\btm\b", blob):
        return ["lokomotive", "diesellokomotive"]
    if re.search(r"zahnrad|\bhge\b", blob):
        return ["lokomotive", "zahnradlokomotive"]
    if re.search(r"rangier", blob):
        return ["lokomotive", "rangierlokomotive"]
    if re.search(
        r"\belektro|\belektrolok|\buniversallok|\bwerbelok|\bnostalgielok|"
        r"\b(?:h?ge|gem|abe|be|deh|xe)\s*\d|\blok\b|\blokomotive",
        blob,
    ):
        return ["lokomotive", "elektrolokomotive"]
    if re.search(r"güterwagen|güter|knickkessel|kesselwagen|uah|sb-v|lb-v|\bza\b|\bhai", blob):
        return ["gueterwagen"]
    if re.search(r"personenwagen|reisezugwagen|panorama|servicewagen|\bwagen\b", blob):
        return ["personenwagen"]
    return ["lokomotive"]


def _description(html: str, title: str) -> str:
    for pat in (
        r'class=["\'][^"\']*product[_-]?description[^"\']*["\'][^>]*>([\s\S]*?)</div>',
        r'class=["\'][^"\']*entry-content[^"\']*["\'][^>]*>([\s\S]*?)</div>',
        r'itemprop=["\']description["\'][^>]*>([\s\S]*?)</(?:div|p|span)>',
    ):
        m = re.search(pat, html, re.I)
        if m:
            text = _plain(m.group(1))
            if len(text) > 20:
                return text
    og = _meta(html, "og:description")
    if og:
        return swiss_ss(og.strip())
    return title or "Unbekannt"


def _image(html: str, base: str, article: str) -> Optional[str]:
    img = _meta(html, "og:image")
    if img:
        if img.startswith("//"):
            return "https:" + img
        if img.startswith("http"):
            return img
        return urljoin(base, img)
    compact = compact_sku(article)
    spaced = spaced_sku(article).replace(" ", "")
    for m in re.finditer(r"<img\b[^>]+>", html, re.I):
        tag = m.group(0)
        sm = re.search(r'\b(?:src|data-src)=["\']([^"\']+)["\']', tag, re.I)
        if not sm:
            continue
        src = sm.group(1)
        blob = (tag + " " + src).lower()
        if compact in blob or spaced in blob or "wp-content/uploads" in blob:
            if src.startswith("//"):
                return "https:" + src
            if src.startswith("http"):
                return src
            return urljoin(base, src)
    return None




def _stamped_pdp_url(html: str) -> Optional[str]:
    m = re.search(r"<!--\s*locobox-pdp-url:\s*(\S+)\s*-->", html)
    return m.group(1).strip() if m else None


def _scale_from_article(article: str, fallback: str) -> str:
    art = compact_sku(article)
    if len(art) >= 2:
        pref = art[:2]
        if pref in {"92", "93", "95", "99"}:
            return "0m"
        if pref in {"10", "11"}:
            return "H0e"
        if pref in {"12", "13", "22", "32"}:
            return "H0m"
    return fallback


def _electric_from_article(article: str, fallback: str) -> str:
    art = compact_sku(article)
    if len(art) >= 2 and art[:2] in {"13", "11", "93", "99"}:
        return "DC-Digital"
    if len(art) >= 2 and art[:2] in {"12", "10", "92", "22", "32", "95"}:
        if fallback.startswith(("DC-Digital", "AC-Digital")):
            return fallback
        return "DC-Analog"
    return fallback


def _split_title(title: str) -> tuple[str, Optional[str], Optional[str]]:
    """Split RhB Ge 4/4 II 614 Universallok \"Schiers\" into type/number/livery."""
    t = swiss_ss(title or "").strip()
    if not t:
        return "Unbekannt", None, None
    livery = None
    qm = re.search(r"[\"“”«»](.+?)[\"“”«»]", t)
    if qm:
        livery = qm.group(1).strip() or None
        t = (t[: qm.start()] + t[qm.end() :]).strip()
    t2 = re.sub(
        r"^(?:RhB|MGB|MOB|DFB|FO|BVZ|DR|DRG|DB(?:\s+AG)?|ÖBB|OBB|StLB|ZB|"
        r"K\.?\s*Sä\.?\s*Sts\.?\s*B\.?|K\.?\s*Sae\.?\s*Sts\.?\s*B\.?)\s+",
        "",
        t,
        flags=re.I,
    ).strip() or t
    m = re.search(
        r"^(?P<typ>(?:H?Ge|Gmf|Gem|Te|Tm|ABe|Be|Deh|Xe|VL|D)\s*\d(?:/\d)?(?:\s*[IVX]+)?)\s+"
        r"(?P<num>\d{1,5}(?:-\d)?)\b(?P<rest>.*)$",
        t2,
        re.I,
    )
    if m:
        typ = re.sub(r"\s+", " ", m.group("typ")).strip()
        num = m.group("num").strip()
        rest = m.group("rest").strip(" -–,")
        role = re.match(
            r"^(Universallok|Zahnradlok|Diesellok|Dampflok(?:-Fertigmodell)?|Werbelok|Nostalgielok|Rangierlok)\b",
            rest,
            re.I,
        )
        if role:
            typ = f"{typ} {role.group(1)}".strip()
        return typ, num, livery
    m = re.search(
        r"^(?P<typ>(?:Uah|Za|Sb-v|Lb-v|Hai(?:qq)?(?:-tuyz)?|Api|Ap|Bp|WRp|WR-?S|WR|A|AB|B|D)\b[^\d]{0,24}?)\s*"
        r"(?P<num>\d{3,5})\b",
        t2,
        re.I,
    )
    if m:
        typ = re.sub(r"\s+", " ", m.group("typ")).strip(" -–")
        return typ, m.group("num"), livery
    m = re.search(r"^(?:DR\s*)?99\s+(\d{3,4}(?:-\d)?)\b", t2, re.I)
    if m:
        rest = t2[m.end() :].strip(" -–,")
        typ = "DR 99"
        role = re.match(r"^(Dampflok(?:-Fertigmodell)?)\b", rest, re.I)
        if role:
            typ = f"{typ} {role.group(1)}".strip()
        return typ, m.group(1), livery
    m = re.search(r"^(?:No\.?\s*)(\d{1,3})\b", t2, re.I)
    if m:
        return "No.", m.group(1), livery
    # Class designations without separate running number (VL 23, D 10, …)
    if re.match(r"^(?:VL|D|Te|Tm)\s*\d+\b", t2, re.I):
        return re.sub(r"\s+", " ", t2).strip(), None, livery
    return t2 or t, None, livery


def parse_bemo_pdp(
    html: str,
    *,
    canonical_url: str,
    article: str,
    campaign_tag: Optional[str] = None,
    uvp_amount: Optional[float] = None,
) -> dict[str, Any]:
    """
    Map bemo-modellbahn.de WordPress PDP into a Locobox article dict.

    Article numbers appear spaced in ``.single_artnr``; Locobox stores digits only.
    """
    wanted = compact_sku(article)
    found = extract_artnr(html)
    if found and found != wanted:
        raise ValueError(f"shop article {found} != requested {wanted}")

    title = _product_title(html, wanted)
    desc = _description(html, title)
    blob = f"{title}\n{desc}\n{_plain(html[:8000])}"
    scale, era = _scale_era_from_text(blob)
    scale = _scale_from_article(wanted, scale)
    operator, country = _operator_country(f"{title}\n{desc}")
    electric = _electric_from_article(wanted, _electric_from_text(blob))
    model_type, model_number, livery = _split_title(title)
    cats = _categories(title, desc)
    if re.search(r"\b(Uah|Za|Sb-v|Lb-v|Hai)\b", title, re.I):
        cats = ["gueterwagen"]
    elif re.search(r"\b(Api|Ap|Bp|WRp|WR|EW|Personen|Panorama|Servicewagen)\b", title, re.I):
        cats = ["personenwagen"]
    if cats and cats[0] in {"gueterwagen", "personenwagen"}:
        electric = "Unbekannt"

    price = uvp_amount if uvp_amount is not None else _uvp_from_html(html)
    if price is not None and float(price) <= 0:
        price = None

    stamped = _stamped_pdp_url(html)
    canon = (stamped or _meta(html, "og:url") or canonical_url or "").split("#")[0].strip()
    if not canon or "?s=" in canon:
        from locobox_cli.adapters.sources.bemo.shop_site import BemoShopSite

        canon = stamped or BemoShopSite().search_url(wanted)
    img = _image(html, canon or "https://www.bemo-modellbahn.de/", wanted)

    tags: list[str] = []
    release = None
    if campaign_tag and campaign_tag.strip():
        tags.append(campaign_tag.strip())
        ym = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", campaign_tag)
        if ym:
            release = ym.group(1)

    source: dict[str, Any] = {
        "url": canon,
        "notes": "Daten von bemo-modellbahn.de, automatisch geupdated.",
    }
    if img and img.startswith("https://"):
        source["imageUrl"] = img

    return {
        "schemaVersion": "1.0.0",
        "id": f"bemo-{wanted}",
        "manufacturer": "BEMO",
        "articleNumber": wanted,
        "releaseDate": release,
        "uvp": {"amount": float(price), "currency": "EUR"} if price is not None else None,
        "model": {
            "country": country,
            "operator": operator,
            "type": model_type or title or "Unbekannt",
            "number": model_number,
            "livery": livery,
            "scale": scale,
            "electricSystem": electric,
            "era": era,
        },
        "description": desc,
        "categories": cats,
        "tags": tags,
        "source": source,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
