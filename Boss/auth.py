from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import BrowserContext, Error, Page

from .browser import acquire_page, release_page, save_storage_state
from .config import HOME_URL, LOGIN_URL, NAVIGATION_WAIT_UNTIL


def ensure_login(context: BrowserContext, session_path: Path) -> bool:
    existing_logged_in_page = find_logged_in_page(context)
    if existing_logged_in_page is not None:
        print(f"Detected logged-in page: {existing_logged_in_page.url}")
        save_storage_state(context, session_path)
        return False

    page, owned = acquire_page(context)
    try:
        if session_path.exists():
            try:
                open_entry_page(page, prefer_login=False)
                if is_logged_in(page):
                    return False
            except Exception:
                pass

        open_entry_page(page, prefer_login=True)
        print(f"Opened page: {page.url}")
        print("Please complete Boss login or verification in the opened browser window.")
        input("After login is complete, press Enter here to continue...")

        detected_page = find_logged_in_page(context) or (page if is_logged_in(page) else None)
        if detected_page is None:
            raise RuntimeError(
                f"Login was not detected. Current page is: {page.url}. "
                "Please confirm you have completed login and are no longer on the login page."
            )

        print(f"Login detected at: {detected_page.url}")
        save_storage_state(context, session_path)
        return True
    finally:
        release_page(page, owned)


def open_entry_page(page: Page, prefer_login: bool) -> None:
    urls = [LOGIN_URL, HOME_URL] if prefer_login else [HOME_URL, LOGIN_URL]
    errors: list[str] = []

    for url in urls:
        try:
            page.goto(url, wait_until="commit")
            page.wait_for_load_state(NAVIGATION_WAIT_UNTIL, timeout=15_000)
            if page.url and page.url != "about:blank":
                return
        except Error as exc:
            errors.append(f"{url}: {exc}")

    joined = " | ".join(errors) if errors else "navigation stayed on about:blank"
    raise RuntimeError(f"Unable to open Boss login page. {joined}")


def is_logged_in(page: Page) -> bool:
    try:
        current_url = page.url or ""
        parsed = urlparse(current_url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()

        if current_url == "about:blank":
            return False
        if "login.zhipin.com" in host:
            return False
        if "security-check" in path or "verify-slider" in path:
            return False

        cookies = page.context.cookies()
        cookie_names = {cookie["name"] for cookie in cookies}
        if not {"wt2", "wbg", "token", "__zp_stoken__"} & cookie_names:
            return False

        return "zhipin.com" in host
    except Error:
        return False


def find_logged_in_page(context: BrowserContext) -> Page | None:
    for page in reversed(context.pages):
        try:
            if is_logged_in(page):
                return page
        except Exception:
            continue
    return None
