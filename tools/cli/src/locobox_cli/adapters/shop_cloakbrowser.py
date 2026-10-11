from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from locobox_cli.adapters.sources.shop_site import ShopSite
from locobox_cli.domain.delay import DelayPolicy


@dataclass(frozen=True, slots=True)
class FetchItemResult:
    article: str
    ok: bool
    path: Optional[Path] = None
    url: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False


@dataclass
class FetchSummary:
    ok: int = 0
    fail: int = 0
    skipped: int = 0
    blocked: bool = False
    results: list[FetchItemResult] | None = None

    def __post_init__(self) -> None:
        if self.results is None:
            self.results = []


def _dismiss_cookies(page) -> None:
    for text in ("Alle akzeptieren", "Akzeptieren", "Accept all", "Accept", "Zustimmen"):
        try:
            loc = page.get_by_role("button", name=text)
            if loc.count() > 0:
                loc.first.click(timeout=2000)
                return
        except Exception:
            continue


def _html_has_article_sku(html: str, article: str) -> bool:
    """True when PDP HTML marks ``article`` as the product SKU (not a substring hit)."""
    art = article.strip()
    if not art:
        return False
    markers = (
        f'"sku":"{art}"',
        f"Artikelnummer: <span>{art}</span>",
        f'Artikelnummer:</td><td class="attribute-value">{art}</td>',
    )
    return any(m in html for m in markers)


def _is_piko_artikel_url(url: str) -> bool:
    if not url:
        return False
    u = url.split("#")[0].split("?", 1)[0].lower()
    return "piko-shop" in u and "/artikel/" in u and u.endswith(".html")


def _redirect_pdp_url(page, site: ShopSite, article: str) -> Optional[str]:
    """Search often lands directly on a PDP (Piko redirect / Roco Magento)."""
    url = (page.url or "").split("#", 1)[0].split("?", 1)[0]
    if site.slug == "piko":
        if not _is_piko_artikel_url(url):
            return None
        try:
            html = page.content()
        except Exception:
            return None
        if not _html_has_article_sku(html, article):
            return None
        return url
    if site.slug == "roco":
        if site.is_pdp_url(url, article):
            return url
        return None
    return None


def _find_pdp_href(page, site: ShopSite, article: str) -> Optional[str]:
    links = page.eval_on_selector_all(
        "a[href]",
        """els => els.map(a => a.href).filter(Boolean)""",
    )
    for href in links:
        if site.is_pdp_url(href, article):
            return href
    return _redirect_pdp_url(page, site, article)


def _looks_blocked(page) -> bool:
    try:
        title = (page.title() or "").lower()
        body = page.inner_text("body")[:2000].lower()
    except Exception:
        return False
    markers = ("captcha", "access denied", "rate limit", "zu viele anfragen", "blocked", "cloudflare")
    blob = title + " " + body
    return any(m in blob for m in markers)


def _roco_form_search(page, article: str) -> bool:
    """Fallback if catalogsearch URL yields no PDP links."""
    try:
        el = page.query_selector("#search, input[name='q']")
        if not el:
            return False
        el.fill(article)
        page.keyboard.press("Enter")
        return True
    except Exception:
        return False


class CloakShopFetcher:
    """Fetch PDP HTML via CloakBrowser for a ShopSite strategy."""

    def __init__(
        self,
        *,
        site: ShopSite,
        html_dir: Path,
        delay: DelayPolicy,
        headless: bool = True,
        humanize: bool = False,
        on_wait: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.site = site
        self.html_dir = html_dir
        self.delay = delay
        self.headless = headless
        self.humanize = humanize
        self.on_wait = on_wait or time.sleep

    def _wait(self) -> None:
        self.on_wait(self.delay.next_seconds())

    def fetch_many(
        self,
        articles: list[str],
        *,
        skip_existing: bool = True,
    ) -> FetchSummary:
        from cloakbrowser import launch

        summary = FetchSummary()
        self.html_dir.mkdir(parents=True, exist_ok=True)

        launch_kwargs: dict = {"headless": self.headless}
        if self.humanize:
            launch_kwargs["humanize"] = True

        browser = launch(**launch_kwargs)
        try:
            page = browser.new_page()
            cookies_done = False
            for art in articles:
                out = self.html_dir / f"{art}.html"
                if skip_existing and out.is_file() and out.stat().st_size > 500:
                    summary.skipped += 1
                    summary.results.append(
                        FetchItemResult(article=art, ok=True, path=out, skipped=True)
                    )
                    continue
                try:
                    page.goto(self.site.search_url(art), wait_until="domcontentloaded", timeout=60000)
                    self._wait()
                    if not cookies_done:
                        _dismiss_cookies(page)
                        cookies_done = True
                        self._wait()
                    if _looks_blocked(page):
                        summary.blocked = True
                        summary.fail += 1
                        summary.results.append(
                            FetchItemResult(article=art, ok=False, error="blocked")
                        )
                        break
                    href = _find_pdp_href(page, self.site, art)
                    if not href and self.site.slug == "roco":
                        page.goto("https://www.roco.cc/rde/", wait_until="domcontentloaded", timeout=60000)
                        self._wait()
                        if _roco_form_search(page, art):
                            self._wait()
                            href = _find_pdp_href(page, self.site, art)
                    if not href:
                        summary.fail += 1
                        summary.results.append(
                            FetchItemResult(article=art, ok=False, error="no_pdp_link")
                        )
                        continue
                    # Search may already have landed on the PDP (common for Roco).
                    already = (page.url or "").split("#", 1)[0].split("?", 1)[0]
                    if already.rstrip("/") != href.split("#", 1)[0].split("?", 1)[0].rstrip("/"):
                        page.goto(href, wait_until="domcontentloaded", timeout=60000)
                        self._wait()
                    if _looks_blocked(page):
                        summary.blocked = True
                        summary.fail += 1
                        summary.results.append(
                            FetchItemResult(article=art, ok=False, error="blocked", url=href)
                        )
                        break
                    html = page.content()
                    if len(html) < 500:
                        summary.fail += 1
                        summary.results.append(
                            FetchItemResult(article=art, ok=False, error="html_too_short", url=href)
                        )
                        continue
                    out.write_text(html, encoding="utf-8")
                    summary.ok += 1
                    summary.results.append(
                        FetchItemResult(article=art, ok=True, path=out, url=href)
                    )
                except Exception as exc:  # noqa: BLE001
                    summary.fail += 1
                    summary.results.append(
                        FetchItemResult(article=art, ok=False, error=str(exc))
                    )
        finally:
            browser.close()
        return summary


# Back-compat alias
CloakPikoFetcher = CloakShopFetcher
