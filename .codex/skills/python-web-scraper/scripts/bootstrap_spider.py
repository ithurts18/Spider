#!/usr/bin/env python3
"""
Generate a minimal Python scraper skeleton.

Examples:
    python bootstrap_spider.py my_spider --mode static
    python bootstrap_spider.py product_api --mode api --output-dir D:\\aiSpider
    python bootstrap_spider.py member_area --mode playwright
"""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


TEMPLATES = {
    "static": dedent(
        '''\
        import csv
        from pathlib import Path

        import requests
        from bs4 import BeautifulSoup


        BASE_URL = "https://example.com"
        START_URL = "https://example.com/list"
        OUTPUT_CSV = Path("{name}.csv")
        TIMEOUT = 20


        def fetch(url: str) -> str:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text


        def parse_list(html: str) -> list[dict]:
            soup = BeautifulSoup(html, "html.parser")
            items = []
            for card in soup.select(".item"):
                title_node = card.select_one(".title")
                link_node = card.select_one("a")
                items.append(
                    {{
                        "title": title_node.get_text(strip=True) if title_node else "",
                        "url": link_node["href"] if link_node and link_node.has_attr("href") else "",
                    }}
                )
            return items


        def save_rows(rows: list[dict]) -> None:
            if not rows:
                return
            with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)


        def main() -> None:
            html = fetch(START_URL)
            rows = parse_list(html)
            save_rows(rows)
            print(f"saved {{len(rows)}} rows to {{OUTPUT_CSV}}")


        if __name__ == "__main__":
            main()
        '''
    ),
    "api": dedent(
        '''\
        import json
        import time
        from pathlib import Path

        import requests


        API_URL = "https://example.com/api/items"
        OUTPUT_JSONL = Path("{name}.jsonl")
        TIMEOUT = 20


        def fetch_page(page: int) -> dict:
            response = requests.get(
                API_URL,
                params={{"page": page}},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()


        def parse_items(payload: dict) -> list[dict]:
            return payload.get("items", [])


        def append_items(items: list[dict]) -> None:
            with OUTPUT_JSONL.open("a", encoding="utf-8") as fh:
                for item in items:
                    fh.write(json.dumps(item, ensure_ascii=False) + "\\n")


        def main() -> None:
            page = 1
            total = 0
            while True:
                payload = fetch_page(page)
                items = parse_items(payload)
                if not items:
                    break
                append_items(items)
                total += len(items)
                page += 1
                time.sleep(1)
            print(f"saved {{total}} items to {{OUTPUT_JSONL}}")


        if __name__ == "__main__":
            main()
        '''
    ),
    "playwright": dedent(
        '''\
        import json
        from pathlib import Path

        from playwright.sync_api import sync_playwright


        TARGET_URL = "https://example.com"
        OUTPUT_JSON = Path("{name}.json")


        def capture_api_payload() -> dict:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                response = page.wait_for_response(
                    lambda r: "/api/" in r.url and r.status == 200
                )
                page.goto(TARGET_URL, wait_until="domcontentloaded")
                payload = response.json()

                browser.close()
                return payload


        def main() -> None:
            payload = capture_api_payload()
            OUTPUT_JSON.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"saved payload to {{OUTPUT_JSON}}")


        if __name__ == "__main__":
            main()
        '''
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a Python scraper file.")
    parser.add_argument("name", help="Output file stem, for example douban_top250")
    parser.add_argument(
        "--mode",
        choices=sorted(TEMPLATES),
        default="static",
        help="Skeleton type to generate",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for the generated .py file",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.name}.py"

    if output_path.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {output_path}")

    content = TEMPLATES[args.mode].format(name=args.name)
    output_path.write_text(content, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
