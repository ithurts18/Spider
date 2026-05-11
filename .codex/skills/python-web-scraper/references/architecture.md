# Scraper Architecture

## Decision Table

| Situation | Preferred path | Notes |
| --- | --- | --- |
| Public JSON endpoint exists | `requests` / `httpx` | Best default for scale and stability |
| HTML already contains target fields | HTTP + HTML parser | Avoid browser overhead |
| Data is injected into page state | HTTP + parse inline JSON | Often easier than DOM scraping |
| Content appears only after JS | Playwright inspect, then reduce | Capture the API if possible |
| Login creates browser-only session | Playwright for login, then export cookies/storage | Reuse auth in HTTP client when possible |
| Infinite scroll with hidden API | Observe network calls | Reproduce cursor requests directly |

## Minimal Project Shape

Use a structure close to this:

```python
def fetch_list_page(...): ...
def parse_list_page(...): ...
def fetch_detail(...): ...
def parse_detail(...): ...
def save_items(...): ...
def main(): ...
```

Keep these concerns separate:

- Transport: request sending, retries, headers, cookies
- Parsing: HTML/JSON extraction only
- Flow control: pagination, dedupe, resumability
- Storage: CSV, JSONL, SQLite

## Field Design

Define a stable schema before broad crawling:

- `source_url`
- `source_id`
- `title`
- `price` or domain-specific numeric fields
- `published_at` or crawl timestamps
- `raw_category` or source taxonomies

Keep source-native fields when they help future reconciliation.

## Reliability Rules

- Set explicit timeout values.
- Use bounded retries with backoff.
- Detect empty result sets as potential failures, not automatic success.
- Log enough context to reproduce a failed page or item.
- Keep a small fixture sample when selectors are fragile.

## Persistence Choices

- Use JSONL for append-only event-like data.
- Use CSV for flat tabular exports that will be opened manually.
- Use SQLite when you need `INSERT OR REPLACE`, unique keys, resume support, or multi-step enrichment.

## Common Failure Modes

- Response differs from browser because of missing cookies or headers.
- Parser targets presentation DOM instead of stable embedded data.
- Pagination loops due to repeated next token.
- Browser automation waits for the wrong readiness signal.
- Deduplication happens after persistence rather than before write.
