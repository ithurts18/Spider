from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, BrowserType, Error, Page, Playwright, sync_playwright

from .config import (
    DEBUG_ENDPOINT,
    EDGE_EXECUTABLE_PATH,
    HEADLESS,
    PAGE_TIMEOUT_MS,
    PROFILE_DIR,
)


WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 960
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
)


def start_playwright() -> Playwright:
    return sync_playwright().start()


def launch_browser(
    playwright: Playwright,
    headless: bool = HEADLESS,
    attach: bool = False,
) -> tuple[BrowserContext, Browser | None]:
    if attach:
        browser = playwright.chromium.connect_over_cdp(DEBUG_ENDPOINT)
        contexts = browser.contexts
        context = contexts[0] if contexts else browser.new_context()
        context.set_default_timeout(PAGE_TIMEOUT_MS)
        return context, browser

    context = launch_persistent_context(playwright.chromium, headless=headless)
    return context, context.browser


def launch_persistent_context(browser_type: BrowserType, headless: bool = HEADLESS) -> BrowserContext:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    launch_kwargs = {
        "user_data_dir": str(PROFILE_DIR),
        "headless": headless,
        "viewport": {"width": WINDOW_WIDTH, "height": WINDOW_HEIGHT},
        "screen": {"width": WINDOW_WIDTH, "height": WINDOW_HEIGHT},
        "user_agent": USER_AGENT,
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
        "color_scheme": "light",
        "args": [
            "--disable-blink-features=AutomationControlled",
            f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}",
        ],
    }

    if EDGE_EXECUTABLE_PATH.exists():
        launch_kwargs["executable_path"] = str(EDGE_EXECUTABLE_PATH)

    context = browser_type.launch_persistent_context(**launch_kwargs)
    context.set_default_timeout(PAGE_TIMEOUT_MS)
    add_init_script(context)
    return context


def add_init_script(context: BrowserContext) -> None:
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'language', {
            get: () => 'zh-CN'
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
        window.chrome = window.chrome || { runtime: {} };
        """
    )


def create_context(
    browser_or_context: BrowserContext,
    session_path: Path | None = None,
    force_login: bool = False,
) -> BrowserContext:
    return browser_or_context


def acquire_page(context: BrowserContext) -> tuple[Page, bool]:
    try:
        page = context.new_page()
        page.set_default_timeout(PAGE_TIMEOUT_MS)
        return page, True
    except Error as exc:
        page = find_reusable_page(context)
        if page is None:
            raise RuntimeError(f"Unable to create or reuse a browser tab: {exc}") from exc
        page.set_default_timeout(PAGE_TIMEOUT_MS)
        return page, False


def release_page(page: Page, owned: bool) -> None:
    if not owned:
        return
    try:
        page.close()
    except Exception:
        return


def find_reusable_page(context: BrowserContext) -> Page | None:
    preferred: list[Page] = []
    fallback: list[Page] = []

    for page in context.pages:
        try:
            current_url = page.url or ""
            if current_url == "about:blank":
                fallback.append(page)
                continue

            host = urlparse(current_url).netloc.lower()
            if "zhipin.com" in host:
                preferred.append(page)
            else:
                fallback.append(page)
        except Exception:
            continue

    if preferred:
        return preferred[-1]
    if fallback:
        return fallback[-1]
    return None


def save_storage_state(context: BrowserContext, session_path: Path | None = None) -> None:
    return None
