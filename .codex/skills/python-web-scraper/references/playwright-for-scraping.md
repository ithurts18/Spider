# Playwright for Scraping

## Use Playwright Sparingly

Use Playwright when the browser is necessary to:

- complete interactive login
- trigger client-side rendering
- capture hidden API calls
- obtain cookies, tokens, or local storage values
- reach content gated behind scripted interactions

If the network panel reveals a stable JSON endpoint, switch the heavy crawl back to plain HTTP.

## High-Value Playwright Tasks

### Inspect network

- watch requests after page load
- capture XHR/fetch URLs, methods, headers, payloads
- identify pagination cursors and auth tokens

### Stabilize page state

- wait for a specific response or selector, not arbitrary sleep
- snapshot page HTML only after the target data is present

### Export authenticated state

- save cookies or storage state after login
- replay them in `requests.Session()` or `httpx.Client()` when feasible

## Practical Patterns

### Wait for the useful response

```python
response = page.wait_for_response(lambda r: "/api/" in r.url and r.status == 200)
page.goto(target_url, wait_until="domcontentloaded")
data = response.json()
```

### Capture storage state

```python
context.storage_state(path="auth.json")
```

### Reuse cookies in requests

Extract cookies from the browser context, then populate a session cookie jar for non-browser fetches.

## Avoid

- scraping large volumes from rendered DOM when the same data exists in JSON
- relying on long `sleep()` calls for readiness
- coupling selectors to visual layout when data attributes or APIs exist
- keeping the whole crawl inside Playwright if only login required the browser
