from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from .browser import create_context, launch_browser, start_playwright
    from .config import (
        DEFAULT_CITIES,
        DEFAULT_JOB_KEYWORDS,
        DEFAULT_LIMIT_PER_CITY,
        DEFAULT_OUTPUT_PATH,
        DEBUG_ENDPOINT,
        DEBUG_PORT,
        EDGE_EXECUTABLE_PATH,
        PROFILE_DIR,
    )
    from .crawler import run_crawl
    from .utils import configure_logging
except ImportError:
    PACKAGE_ROOT = Path(__file__).resolve().parent.parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.insert(0, str(PACKAGE_ROOT))
    from Boss.browser import create_context, launch_browser, start_playwright
    from Boss.config import (
        DEFAULT_CITIES,
        DEFAULT_JOB_KEYWORDS,
        DEFAULT_LIMIT_PER_CITY,
        DEFAULT_OUTPUT_PATH,
        DEBUG_ENDPOINT,
        DEBUG_PORT,
        EDGE_EXECUTABLE_PATH,
        PROFILE_DIR,
    )
    from Boss.crawler import run_crawl
    from Boss.utils import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Boss zhipin training scraper")
    parser.add_argument(
        "--cities",
        nargs="+",
        default=list(DEFAULT_CITIES.keys()),
        help="Cities to crawl. Default: 北京 上海 深圳",
    )
    parser.add_argument(
        "--job-keywords",
        nargs="+",
        default=DEFAULT_JOB_KEYWORDS,
        help="Job keywords. Default: Python 数据分析 产品经理",
    )
    parser.add_argument(
        "--limit-per-city",
        type=int,
        default=DEFAULT_LIMIT_PER_CITY,
        help="Maximum number of rows to keep for each city",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Excel output path",
    )
    parser.add_argument(
        "--force-login",
        action="store_true",
        help="Ignore saved session state and force a fresh login",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Launch browser in headless mode",
    )
    parser.add_argument(
        "--attach-edge",
        action="store_true",
        help="Attach to a manually started Edge debug session",
    )
    return parser


def resolve_cities(city_names: list[str]) -> dict[str, str]:
    invalid = [name for name in city_names if name not in DEFAULT_CITIES]
    if invalid:
        raise SystemExit(f"Unsupported cities: {', '.join(invalid)}")
    return {name: DEFAULT_CITIES[name] for name in city_names}


def print_attach_help() -> None:
    print("Attach mode is enabled.")
    print(f"Start Edge manually with remote debugging port {DEBUG_PORT}.")
    print(f"Edge executable: {EDGE_EXECUTABLE_PATH}")
    print(f"Debug endpoint: {DEBUG_ENDPOINT}")
    print(f"Suggested user data dir: {PROFILE_DIR}")


def main() -> None:
    args = build_parser().parse_args()
    logger = configure_logging()
    cities = resolve_cities(args.cities)

    if args.attach_edge:
        print_attach_help()

    playwright = start_playwright()
    context, browser = launch_browser(playwright, headless=args.headless, attach=args.attach_edge)
    context = create_context(context, force_login=args.force_login)

    try:
        result = run_crawl(
            cities=cities,
            job_keywords=args.job_keywords,
            limit_per_city=args.limit_per_city,
            output_path=args.output,
            force_login=args.force_login,
            context=context,
            logger=logger,
        )
    except Exception as exc:
        print(f"Run failed: {exc}")
        if not args.headless:
            try:
                input("Press Enter to close the browser...")
            except EOFError:
                pass
        raise
    finally:
        context.close()
        if browser is not None and browser.is_connected() and not args.attach_edge:
            browser.close()
        playwright.stop()

    print(f"Output file: {result['output_path']}")
    print(f"Success: {result['summary'].get('success', 0)}")
    print(f"Skipped: {result['summary'].get('skipped', 0)}")
    print(f"Failed: {result['summary'].get('failed', 0)}")
    if result["failures"]:
        print("Failure summary:")
        for failure in result["failures"][:10]:
            print(f"- {failure}")


if __name__ == "__main__":
    main()
