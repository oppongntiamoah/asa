"""
Automated pull of daily closing prices from GSE's own website, reusing
csv_ingest.ingest_price_csv() rather than duplicating its parsing/dedup
logic — this module's only job is turning GSE's response into the same
CSV shape a manually-uploaded file already has.

Verified against the real endpoint (2026-07-23, via a captured browser
request — see conversation history, not reproduced here since credentials/
cookies aren't committed to source): GSE's "Daily Shares & ETFs" table at
https://gse.com.gh/trading-and-data/ is powered by the wpDataTables
WordPress plugin (table_id=39), which exposes a standard DataTables.net
server-side-processing endpoint at
POST https://gse.com.gh/wp-admin/admin-ajax.php?action=get_wdtable&table_id=39

Two real risks this design has to account for, not just "the request
works today":

1. Cloudflare. The site sits behind Cloudflare bot protection
   (cf_clearance/__cf_bm cookies observed). A plain requests.Session
   making a cold GET+POST from a VPS IP with no prior browser trust may
   get challenged instead of served real data — untested from a
   VPS/production IP as of writing. This module fails loudly (raises
   GSEScraperError) rather than silently treating a challenge page as
   valid data, and the caller (see instruments/tasks.py) must fall back
   to prompting for a manual CSV upload rather than leaving stale prices
   in place unnoticed. If Cloudflare blocking turns out to be a hard
   blocker in practice, the honest fix is switching this fetch to run
   through a real headless browser (Playwright) instead of `requests` —
   deliberately not built that way up front since it's meaningfully more
   infrastructure (a browser on the VPS) than everything else in this
   app, and not worth adding until the plain-HTTP approach is confirmed
   to fail.

2. wdtNonce. wpDataTables requires a per-page-load nonce token in the
   POST body, embedded somewhere in the page's HTML/inline JS. The exact
   embedding pattern wasn't confirmed against real page source at the
   time this was written (only the POST payload was captured, not the
   page that generates it) — _extract_nonce() tries a few known
   wpDataTables conventions and raises clearly if none match, rather than
   guessing and sending a stale/empty nonce.

Rather than trust a date filter parameter whose exact accepted format
wasn't verified, this fetches rows sorted by date descending and keeps
only whichever date is most recent in the response — self-adjusting for
weekends/holidays without needing to know "today" has data in advance.
"""
import csv
import io
import re

import requests

from .csv_ingest import IngestResult, ingest_price_csv

GSE_PAGE_URL = "https://gse.com.gh/trading-and-data/"
GSE_AJAX_URL = "https://gse.com.gh/wp-admin/admin-ajax.php?action=get_wdtable&table_id=39"
TABLE_ID = 39

# columns[1..13] — order and names verified against a real captured request;
# column 0 (wdt_ID) is an internal row id, not part of the CSV shape.
COLUMN_NAMES = [
    "dailydate", "sharecode", "yearhighgh", "yearlowgh",
    "previousclosingpricevwapgh", "openingpricegh", "lasttransactionpricegh",
    "closingpricevwapgh", "pricechangegh", "closingbidpricegh",
    "closingofferpricegh", "totalsharestraded", "totalvaluetradedgh",
]

# Matches csv_ingest.py's expected header row exactly, so the reconstructed
# CSV is parsed with zero changes to already-tested logic.
CSV_HEADER = [
    "Daily Date", "Share Code", "Year High (GH¢)", "Year Low (GH¢)",
    "Previous Closing Price - VWAP (GH¢)", "Opening Price (GH¢)",
    "Last Transaction Price (GH¢)", "Closing Price - VWAP (GH¢)",
    "Price Change (GH¢)", "Closing Bid Price (GH¢)", "Closing Offer Price (GH¢)",
    "Total Shares Traded", "Total Value Traded (GH¢)",
]

REQUEST_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://gse.com.gh",
    "Referer": GSE_PAGE_URL,
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Tried in order against the page HTML — wpDataTables has used more than
# one convention for embedding this across versions.
NONCE_PATTERNS = [
    re.compile(r'"wdtNonce"\s*:\s*"([a-f0-9]+)"'),
    re.compile(r"wdtNonce\w*\s*=\s*['\"]([a-f0-9]+)['\"]"),
    re.compile(r'data-wdtnonce=["\']([a-f0-9]+)["\']'),
]


class GSEScraperError(Exception):
    """Raised for anything that means the response can't be trusted as
    real price data — a Cloudflare challenge, a missing nonce, an
    unexpected response shape. Never silently swallowed into a
    zero-row "success"."""


def _extract_nonce(page_html: str) -> str:
    for pattern in NONCE_PATTERNS:
        match = pattern.search(page_html)
        if match:
            return match.group(1)
    raise GSEScraperError(
        "Couldn't find wdtNonce in the GSE trading-and-data page — the page "
        "structure may have changed. Inspect the page source for the new "
        "pattern and update NONCE_PATTERNS in instruments/ingest/scraper.py."
    )


def _build_payload(nonce: str, length: int = 200) -> dict:
    payload = {
        "draw": "1",
        "columns[0][data]": "0",
        "columns[0][name]": "wdt_ID",
        "columns[0][searchable]": "true",
        "columns[0][orderable]": "true",
        "columns[0][search][value]": "",
        "columns[0][search][regex]": "false",
    }
    for i, name in enumerate(COLUMN_NAMES, start=1):
        payload[f"columns[{i}][data]"] = str(i)
        payload[f"columns[{i}][name]"] = name
        payload[f"columns[{i}][searchable]"] = "true"
        payload[f"columns[{i}][orderable]"] = "true"
        payload[f"columns[{i}][search][value]"] = ""
        payload[f"columns[{i}][search][regex]"] = "false"
    payload.update({
        "order[0][column]": "1",  # dailydate
        "order[0][dir]": "desc",
        "start": "0",
        "length": str(length),
        "search[value]": "",
        "search[regex]": "false",
        "wdtNonce": nonce,
    })
    return payload


def fetch_latest_day_rows(session: "requests.Session | None" = None) -> list[list[str]]:
    """
    Returns the raw row lists (13 fields each, matching COLUMN_NAMES order)
    for whichever trading date is most recent in GSE's table. Raises
    GSEScraperError on anything that isn't a clean, parseable success.
    """
    session = session or requests.Session()
    session.headers.update(REQUEST_HEADERS)

    page_resp = session.get(GSE_PAGE_URL, timeout=20)
    if page_resp.status_code != 200:
        raise GSEScraperError(f"GSE page fetch failed: HTTP {page_resp.status_code}")
    nonce = _extract_nonce(page_resp.text)

    ajax_resp = session.post(GSE_AJAX_URL, data=_build_payload(nonce), timeout=20)
    if ajax_resp.status_code != 200:
        raise GSEScraperError(f"GSE data fetch failed: HTTP {ajax_resp.status_code}")

    try:
        payload = ajax_resp.json()
    except ValueError as exc:
        snippet = ajax_resp.text[:300]
        raise GSEScraperError(
            f"GSE data fetch didn't return JSON (likely a Cloudflare challenge page "
            f"or a changed API) — first 300 chars: {snippet!r}"
        ) from exc

    rows = payload.get("data")
    if not rows:
        raise GSEScraperError(f"GSE data fetch returned no rows: {payload!r}")

    # rows are already sorted by dailydate desc (server-side order[0]);
    # keep only the first (most recent) date's worth of rows.
    latest_date = rows[0][1]  # index 1 = dailydate (index 0 is wdt_ID)
    return [row[1:] for row in rows if row[1] == latest_date]


def _rows_to_csv_text(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    writer.writerows(rows)
    return buffer.getvalue()


def scrape_and_ingest(uploaded_by=None) -> IngestResult:
    """Entry point for the scheduled task / management command."""
    rows = fetch_latest_day_rows()
    csv_text = _rows_to_csv_text(rows)
    return ingest_price_csv(io.StringIO(csv_text), trade_date=None, uploaded_by=uploaded_by, source="scrape")
