from __future__ import annotations


def piko_search_url(article: str, *, start_url: str = "https://www.piko-shop.de/de") -> str:
    base = start_url.strip().rstrip("/")
    if "piko-shop" not in base:
        base = "https://www.piko-shop.de/de"
    elif not base.endswith("/de"):
        base = "https://www.piko-shop.de/de"
    return f"{base}/praesenz/search.html?q={article}"


def is_piko_pdp_url(href: str) -> bool:
    if not href or not href.startswith("http"):
        return False
    u = href.split("#")[0].split("?", 1)[0].lower()
    return "piko-shop" in u and "/artikel/" in u and u.endswith(".html")
