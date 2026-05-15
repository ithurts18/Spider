from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from playwright.sync_api import BrowserContext, Page, Response

from .auth import ensure_login
from .browser import acquire_page, release_page, save_storage_state
from .config import (
    DEFAULT_OUTPUT_PATH,
    MAX_PAGES_PER_QUERY,
    MAX_RETRIES,
    NAVIGATION_WAIT_UNTIL,
    NETWORK_IDLE_WAIT_MS,
    RANDOM_DELAY_RANGE,
    SEARCH_URL,
    SESSION_STATE_PATH,
)
from .exporter import export_to_excel
from .models import JobRecord
from .parser import extract_payload_job_rows, parse_job_card
from .utils import sleep_with_jitter, unique_records


def run_crawl(
    cities: dict[str, str],
    job_keywords: list[str],
    limit_per_city: int,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    force_login: bool = False,
    context: BrowserContext | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    if context is None:
        raise ValueError("run_crawl requires an active Playwright browser context.")
    if logger is None:
        raise ValueError("run_crawl requires a configured logger.")

    session_refreshed = ensure_login(context, SESSION_STATE_PATH)
    if session_refreshed:
        logger.info("Login state refreshed and saved.")

    all_records: list[JobRecord] = []
    summary = Counter(success=0, skipped=0, failed=0)
    failures: list[str] = []

    for city_name, city_code in cities.items():
        logger.info("Start crawling city: %s", city_name)
        try:
            city_records, city_summary, city_failures = crawl_city_jobs(
                context=context,
                city=city_name,
                city_code=city_code,
                job_keywords=job_keywords,
                limit_per_city=limit_per_city,
                logger=logger,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("City crawl failed for %s: %s", city_name, exc)
            summary["failed"] += 1
            failures.append(f"{city_name}: {exc}")
            continue

        all_records.extend(city_records)
        summary.update(city_summary)
        failures.extend(city_failures)

    deduped_records = unique_records(all_records)
    export_to_excel(deduped_records, output_path)
    logger.info("Export finished with %s unique rows: %s", len(deduped_records), output_path)

    return {
        "records": deduped_records,
        "summary": dict(summary),
        "failures": failures,
        "output_path": str(output_path),
    }


def crawl_city_jobs(
    context: BrowserContext,
    city: str,
    city_code: str,
    job_keywords: list[str],
    limit_per_city: int,
    logger: logging.Logger,
) -> tuple[list[JobRecord], Counter, list[str]]:
    page, owned = acquire_page(context)
    city_records: list[JobRecord] = []
    summary = Counter(success=0, skipped=0, failed=0)
    failures: list[str] = []

    try:
        for keyword in job_keywords:
            if len(unique_records(city_records)) >= limit_per_city:
                break

            logger.info("City %s keyword %s", city, keyword)
            for page_no in range(1, MAX_PAGES_PER_QUERY + 1):
                if len(unique_records(city_records)) >= limit_per_city:
                    break

                url = build_search_url(keyword, city_code, page_no)
                logger.info("Open search page: %s", url)

                payload_rows: list[dict[str, Any]] = []
                captured_urls: list[str] = []

                def on_response(response: Response) -> None:
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" not in content_type:
                            return
                        payload = response.json()
                        rows = extract_payload_job_rows(payload)
                        if rows:
                            payload_rows.extend(rows)
                            captured_urls.append(response.url)
                    except Exception:  # noqa: BLE001
                        return

                page.on("response", on_response)
                try:
                    navigate_with_retry(page, url, logger)
                    page.wait_for_timeout(NETWORK_IDLE_WAIT_MS)
                    sleep_with_jitter(RANDOM_DELAY_RANGE)
                    raw_rows = payload_rows or extract_dom_rows(page)
                    if not raw_rows:
                        logger.warning(
                            "No usable rows on search page: city=%s keyword=%s page=%s",
                            city,
                            keyword,
                            page_no,
                        )
                        summary["skipped"] += 1
                        break

                    parsed_count = 0
                    for raw_row in raw_rows:
                        try:
                            record = parse_job_card(raw_row, city)
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("Failed to parse job row: %s", exc)
                            summary["failed"] += 1
                            failures.append(f"{city}/{keyword}/page{page_no}: parse failed {exc}")
                            continue

                        if not is_valid_record(record):
                            summary["skipped"] += 1
                            continue

                        city_records.append(record)
                        parsed_count += 1
                        summary["success"] += 1
                        if len(unique_records(city_records)) >= limit_per_city:
                            break

                    logger.info(
                        "City %s keyword %s page %s extracted %s rows, source=%s",
                        city,
                        keyword,
                        page_no,
                        parsed_count,
                        captured_urls[0] if captured_urls else "dom",
                    )

                    if parsed_count == 0:
                        break
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Search page crawl failed: %s", exc)
                    summary["failed"] += 1
                    failures.append(f"{city}/{keyword}/page{page_no}: {exc}")
                    break
                finally:
                    try:
                        page.remove_listener("response", on_response)
                    except Exception:  # noqa: BLE001
                        pass
    finally:
        save_storage_state(context, SESSION_STATE_PATH)
        release_page(page, owned)

    return unique_records(city_records)[:limit_per_city], summary, failures


def build_search_url(keyword: str, city_code: str, page_no: int) -> str:
    query = urlencode({"query": keyword, "city": city_code, "page": page_no})
    return f"{SEARCH_URL}?{query}"


def navigate_with_retry(page: Page, url: str, logger: logging.Logger) -> None:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            page.goto(url, wait_until=NAVIGATION_WAIT_UNTIL)
            if "security-check" in page.url or "verify-slider" in page.url:
                raise RuntimeError("Hit security verification. Complete the check in browser and run again.")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning("Open page failed, attempt %s/%s: %s", attempt, MAX_RETRIES, exc)
            sleep_with_jitter((1.0, 2.0))
    raise RuntimeError(f"Open page failed: {last_error}")


def extract_dom_rows(page: Page) -> list[dict[str, Any]]:
    script = """
    () => {
      const cardSelectors = [
        '.job-card-wrapper',
        '.job-list-box li',
        '.search-job-result .job-card-box',
        '.job-card-box',
        'li[data-key]',
      ];
      let cards = [];
      for (const selector of cardSelectors) {
        const nodes = Array.from(document.querySelectorAll(selector));
        if (nodes.length) {
          cards = nodes;
          break;
        }
      }

      const text = (root, selectors) => {
        for (const selector of selectors) {
          const node = root.querySelector(selector);
          if (node && node.textContent) {
            return node.textContent.replace(/\\s+/g, ' ').trim();
          }
        }
        return '';
      };

      const collectTags = (root) => {
        const selectors = [
          '.tag-list li',
          '.labels-tag span',
          '.job-card-footer li',
          '.job-card-footer span',
          '.job-labels span',
        ];
        const result = [];
        for (const selector of selectors) {
          const nodes = Array.from(root.querySelectorAll(selector));
          for (const node of nodes) {
            const value = node.textContent ? node.textContent.replace(/\\s+/g, ' ').trim() : '';
            if (value) {
              result.push(value);
            }
          }
          if (result.length) {
            break;
          }
        }
        return result;
      };

      const rows = cards.map((card) => {
        const requirements = text(card, [
          '.job-info .tag-list',
          '.job-info .job-labels',
          '.job-card-left .tag-list',
          '.job-info',
        ]);
        return {
          job_name: text(card, ['.job-name', '.job-title', '.job-card-left .job-name', '[class*=job-name]']),
          salary: text(card, ['.salary', '.red', '[class*=salary]']),
          company_name: text(card, ['.company-name', '.boss-name', '[class*=company-name]']),
          requirements,
          skill_keywords: collectTags(card),
        };
      });
      return rows.filter(row => row.job_name || row.salary || row.company_name);
    }
    """
    rows = page.evaluate(script)
    return rows if isinstance(rows, list) else []


def is_valid_record(record: JobRecord) -> bool:
    return bool(record.job_name and record.salary and record.company_name)
