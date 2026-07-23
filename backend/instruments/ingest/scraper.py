"""
Post-MVP: automated pull of daily closing prices from a GSE data source,
producing the same CSV shape csv_ingest.ingest_price_csv() expects so both
paths share one ingestion function. Not implemented — admin CSV upload
(see instruments/admin.py) is the launch path. See PRODUCT_DESIGN.md §2.4.

Tried once (2026-07): GSE's "Daily Shares & ETFs" table is powered by the
wpDataTables WordPress plugin (table_id=39), exposing a DataTables.net
server-side-processing endpoint at
POST https://gse.com.gh/wp-admin/admin-ajax.php?action=get_wdtable&table_id=39
A live curl replay confirmed it returns real JSON data matching the CSV
format already supported. Reverted, though, after the actual blocker
showed up on the first real run: the request requires a per-page-load
wdtNonce token embedded in the page HTML, and none of the embedding
patterns guessed without seeing real page source matched. The site is
also behind Cloudflare (cf_clearance/__cf_bm cookies observed), which is
a separate, likely harder problem for a script running unattended on a
VPS with no prior browser trust — untested, since the nonce extraction
never got past its first failure.

If this gets revisited: get the real page HTML first (view-source or
DevTools) to find the actual nonce pattern before writing extraction code
against it — the same rule that made every other parser in this app
(broker statements, GSE CSV) work on the first real try instead of
several guess-and-check rounds.
"""
