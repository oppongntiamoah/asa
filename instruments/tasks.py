"""Django-Q2 scheduled task for the automated GSE price scrape. See
instruments/ingest/scraper.py for the real caveats (Cloudflare, nonce
extraction) before relying on this running unattended."""
import logging

from .ingest.scraper import GSEScraperError, scrape_and_ingest

logger = logging.getLogger(__name__)


def scheduled_gse_scrape():
    """
    Registered as a daily Django-Q Schedule (see admin: Django Q ->
    Scheduled tasks, or wire one up with django_q.models.Schedule).
    Deliberately does not raise past this point — a scheduled task
    crashing is easy to miss, whereas a PriceIngestBatch with
    error_count set is visible in admin. On a GSEScraperError (Cloudflare
    block, changed page structure, etc.), nothing is ingested and the
    failure is logged clearly so the founder knows to fall back to a
    manual CSV upload for that day rather than leaving stale prices in
    place unnoticed.
    """
    try:
        result = scrape_and_ingest()
    except GSEScraperError:
        logger.exception("GSE scrape failed — falling back to manual CSV upload for today")
        return

    if result.error_count:
        logger.warning(
            "GSE scrape ingested %d rows with %d errors: %s",
            result.row_count, result.error_count, result.errors,
        )
    else:
        logger.info("GSE scrape ingested %d rows cleanly", result.row_count)
