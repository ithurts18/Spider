---
name: python-web-scraper
description: Build, debug, and extend Python web scraping workflows for static pages, JSON APIs, and JavaScript-heavy sites. Use when Codex needs to create or modify Python crawlers, inspect pagination and detail-page flows, persist cookies or login state, extract structured fields, add retry/rate-limit handling, choose between requests and browser automation, or troubleshoot scraping failures caused by dynamic rendering, anti-bot behavior, redirects, or brittle selectors.
---

# Python Web Scraper

## Overview

Use this skill to implement practical Python data collection workflows with the smallest reliable toolset first. Prefer direct HTTP requests and JSON endpoints when possible; escalate to browser automation only when the target actually requires JavaScript execution, authenticated browser state, or network interception.

## Workflow

1. Identify the acquisition path before writing code.
2. Prefer stable sources in this order: JSON/XHR API, embedded page data, server-rendered HTML, browser-rendered DOM.
3. Reproduce the fetch path with the lightest viable Python stack.
4. Normalize extracted items into a clear schema early.
5. Add pagination, retries, throttling, deduplication, and persistence only after one page works.
6. Verify with a small sample run before scaling up.

## Strategy Selection

Choose the implementation path that matches the target:

- Use `requests` or `httpx` for static pages, REST APIs, GraphQL endpoints, or predictable HTML responses.
- Use `BeautifulSoup`, `lxml`, or XPath/CSS selectors for HTML extraction when the data exists in the response body.
- Use Playwright only when content appears after JavaScript execution, the site requires interactive login, the API is hidden behind browser-only flows, or you need to capture requests/responses from the page session.
- Use hybrid flows when page navigation is needed only to obtain cookies, tokens, or hidden API endpoints, then switch back to plain HTTP for scale.

Read [references/architecture.md](references/architecture.md) when deciding which path to use.
Read [references/playwright-for-scraping.md](references/playwright-for-scraping.md) when browser automation is necessary.

## Implementation Rules

- Start from a concrete output schema with explicit field names.
- Keep fetch, parse, pagination, and persistence as separate functions.
- Preserve raw identifiers such as item IDs, source URLs, timestamps, and page numbers.
- Normalize text with trimming and null-handling, but do not silently drop ambiguous values.
- Fail loudly on structural changes that would corrupt data quality.
- Add timeouts, retry limits, and backoff for every network path.
- Respect robots, terms, and legal constraints; do not frame bypass of access controls as a default tactic.

## Recommended Build Order

### 1. Reproduce one successful request

- Capture the exact URL, method, headers, params, cookies, and payload.
- Confirm whether the useful data is in HTML, inline JSON, or XHR responses.
- Save one raw sample response locally during development when that helps debug parsing.

### 2. Parse one record correctly

- Extract one item end-to-end before handling lists.
- Keep selectors close to the data source rather than broad page-wide patterns.
- Prefer structured JSON traversal over regex when both are available.

### 3. Generalize to list pages and detail pages

- Separate list-page item discovery from detail-page enrichment.
- Track seen IDs/URLs to avoid duplicate requests.
- Preserve referential links between list and detail records.

### 4. Add control logic

- Add pagination guards.
- Add rate limiting and jitter.
- Add retry policy with bounded attempts.
- Add checkpointing when large runs may be interrupted.

### 5. Persist results

- Default to JSON Lines or CSV for simple exports.
- Use SQLite when the crawl needs resumability, uniqueness constraints, or incremental updates.
- Write outputs through a dedicated serializer instead of mixing file IO into parser code.

## Browser-Automation Guidance

When a site is dynamic, do not scrape rendered text blindly first. Inspect the network activity and look for:

- JSON endpoints requested after page load
- Cursor or page tokens in XHR/fetch calls
- Auth headers or cookies produced after login
- Embedded state blobs in `script` tags or global variables

If the API can be replayed outside the browser, move the high-volume crawl back to Python HTTP clients. Use Playwright only for the minimum browser-only portion.

## Debugging Checklist

- If selectors fail, confirm whether the response is different by region, auth state, or user-agent.
- If fields are empty, inspect raw responses before changing parser logic.
- If pagination stalls, verify next-page tokens and termination conditions.
- If requests are blocked, compare browser and script headers, cookies, and navigation sequence.
- If duplicates appear, define a stable primary key and dedupe before persistence.
- If performance is poor, reduce browser dependence and batch plain HTTP fetches where safe.

## Deliverables

When using this skill, produce:

- Working Python code or a targeted patch
- A short note describing the chosen acquisition strategy
- Any required selectors, endpoint patterns, or request-shaping details
- A verification step such as a sample run, parsed output preview, or schema check

## Bundled Resources

- Use [scripts/bootstrap_spider.py](scripts/bootstrap_spider.py) to generate a minimal scraper skeleton for static pages, JSON APIs, or Playwright-assisted crawls.
- Use [references/architecture.md](references/architecture.md) for strategy and code-organization guidance.
- Use [references/playwright-for-scraping.md](references/playwright-for-scraping.md) for the subset of Playwright patterns that matter to scraping work.
